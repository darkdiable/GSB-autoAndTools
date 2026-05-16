import re
from typing import List, Dict, Tuple, Optional, Union
from dataclasses import dataclass, field
from bs4 import BeautifulSoup
import html

from .toc_extractor import Chapter
from .pdf_parser import PdfImage, TextBlock


@dataclass
class ChapterContent:
    chapter_id: str
    title: str
    html_content: str
    level: int
    order: int
    images: List[PdfImage] = field(default_factory=list)


class ContentProcessor:
    def __init__(self):
        self.image_counter = 0
        self.footnote_counter = 0

    def process_chapters(self, chapters: List[Chapter], pdf_parser) -> List[ChapterContent]:
        contents = []
        flat_chapters = self._flatten_chapters(chapters)
        
        for idx, chapter in enumerate(flat_chapters):
            chapter_id = f'chapter_{idx + 1}'
            content = self._process_single_chapter(chapter, chapter_id, idx, pdf_parser)
            if content:
                contents.append(content)
        
        return contents

    def _flatten_chapters(self, chapters: List[Chapter], level: int = 0) -> List[Chapter]:
        flattened = []
        for chapter in chapters:
            flattened.append(chapter)
            if chapter.children:
                flattened.extend(self._flatten_chapters(chapter.children, level + 1))
        return flattened

    def _process_single_chapter(self, chapter: Chapter, chapter_id: str, order: int, pdf_parser) -> Optional[ChapterContent]:
        if chapter.content_start_page is None or chapter.content_end_page is None:
            return None
        
        text_blocks = pdf_parser.extract_text_blocks(
            chapter.content_start_page,
            chapter.content_end_page
        )
        
        images = pdf_parser.get_images_by_page_range(
            chapter.content_start_page,
            chapter.content_end_page
        )
        
        if not text_blocks and not images:
            return None
        
        html_content = self._blocks_to_html(text_blocks, images, chapter.title, chapter.level)
        
        return ChapterContent(
            chapter_id=chapter_id,
            title=chapter.title,
            html_content=html_content,
            level=chapter.level,
            order=order,
            images=images
        )

    def _blocks_to_html(self, text_blocks: List[TextBlock], images: List[PdfImage], title: str, level: int) -> str:
        html_parts = []
        
        heading_level = min(level + 1, 6)
        html_parts.append(f'<h{heading_level} id="{self._slugify(title)}">{html.escape(title)}</h{heading_level}>')
        
        if not text_blocks and not images:
            return self._wrap_html_document('\n'.join(html_parts), title)
        
        items = self._merge_text_and_images(text_blocks, images)
        
        current_paragraph = []
        
        for item in items:
            if isinstance(item, PdfImage):
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    paragraph_text = self._process_inline_formatting(paragraph_text)
                    html_parts.append(f'<p>{paragraph_text}</p>')
                    current_paragraph = []
                
                img_ext = self._get_image_extension(item.format)
                img_src = f'images/{item.image_id}.{img_ext}'
                img_html = f'<figure class="image-figure"><img src="{img_src}" alt="{item.image_id}" class="chapter-image"/>'
                if item.width > 0 and item.height > 0:
                    img_html = f'<figure class="image-figure"><img src="{img_src}" alt="{item.image_id}" class="chapter-image" width="{item.width}" height="{item.height}"/>'
                img_html += f'<figcaption class="image-caption">图 {item.image_id}</figcaption></figure>'
                html_parts.append(img_html)
            else:
                line = item.text.strip()
                
                if not line:
                    if current_paragraph:
                        paragraph_text = ' '.join(current_paragraph)
                        paragraph_text = self._process_inline_formatting(paragraph_text)
                        html_parts.append(f'<p>{paragraph_text}</p>')
                        current_paragraph = []
                    continue
                
                if self._is_heading(line):
                    if current_paragraph:
                        paragraph_text = ' '.join(current_paragraph)
                        paragraph_text = self._process_inline_formatting(paragraph_text)
                        html_parts.append(f'<p>{paragraph_text}</p>')
                        current_paragraph = []
                    
                    heading_level = self._determine_heading_level(line)
                    heading_text = self._strip_heading_markers(line)
                    html_parts.append(f'<h{heading_level} id="{self._slugify(heading_text)}">{html.escape(heading_text)}</h{heading_level}>')
                    continue
                
                if self._is_list_item(line):
                    if current_paragraph:
                        paragraph_text = ' '.join(current_paragraph)
                        paragraph_text = self._process_inline_formatting(paragraph_text)
                        html_parts.append(f'<p>{paragraph_text}</p>')
                        current_paragraph = []
                    
                    list_text = self._strip_list_markers(line)
                    list_text = self._process_inline_formatting(list_text)
                    html_parts.append(f'<li>{list_text}</li>')
                    continue
                
                if self._is_blockquote(line):
                    if current_paragraph:
                        paragraph_text = ' '.join(current_paragraph)
                        paragraph_text = self._process_inline_formatting(paragraph_text)
                        html_parts.append(f'<p>{paragraph_text}</p>')
                        current_paragraph = []
                    
                    quote_text = self._strip_blockquote_markers(line)
                    quote_text = self._process_inline_formatting(quote_text)
                    html_parts.append(f'<blockquote>{quote_text}</blockquote>')
                    continue
                
                current_paragraph.append(line)
        
        if current_paragraph:
            paragraph_text = ' '.join(current_paragraph)
            paragraph_text = self._process_inline_formatting(paragraph_text)
            html_parts.append(f'<p>{paragraph_text}</p>')
        
        return self._wrap_html_document('\n'.join(html_parts), title)

    def _merge_text_and_images(self, text_blocks: List[TextBlock], images: List[PdfImage]) -> List[Union[TextBlock, PdfImage]]:
        merged = []
        
        for block in text_blocks:
            merged.append(block)
        
        for img in images:
            img_top = img.page_height - img.y1 if img.page_height > 0 else img.y0
            insert_pos = 0
            
            for i, item in enumerate(merged):
                if isinstance(item, PdfImage):
                    item_top = item.page_height - item.y1 if item.page_height > 0 else item.y0
                    if img.page_idx < item.page_idx or (img.page_idx == item.page_idx and img_top < item_top):
                        insert_pos = i
                        break
                else:
                    if img.page_idx < item.page_idx or (img.page_idx == item.page_idx and img_top < item.y0):
                        insert_pos = i
                        break
                insert_pos = i + 1
            
            merged.insert(insert_pos, img)
        
        return merged

    def _text_to_html(self, text: str, title: str, level: int, images: List[PdfImage] = None, chapter_id: str = '') -> str:
        lines = text.split('\n') if text else []
        html_parts = []
        
        heading_level = min(level + 1, 6)
        html_parts.append(f'<h{heading_level} id="{self._slugify(title)}">{html.escape(title)}</h{heading_level}>')
        
        current_paragraph = []
        
        for line in lines:
            line = line.strip()
            
            if not line:
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    paragraph_text = self._process_inline_formatting(paragraph_text)
                    html_parts.append(f'<p>{paragraph_text}</p>')
                    current_paragraph = []
                continue
            
            if self._is_heading(line):
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    paragraph_text = self._process_inline_formatting(paragraph_text)
                    html_parts.append(f'<p>{paragraph_text}</p>')
                    current_paragraph = []
                
                heading_level = self._determine_heading_level(line)
                heading_text = self._strip_heading_markers(line)
                html_parts.append(f'<h{heading_level} id="{self._slugify(heading_text)}">{html.escape(heading_text)}</h{heading_level}>')
                continue
            
            if self._is_list_item(line):
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    paragraph_text = self._process_inline_formatting(paragraph_text)
                    html_parts.append(f'<p>{paragraph_text}</p>')
                    current_paragraph = []
                
                list_text = self._strip_list_markers(line)
                list_text = self._process_inline_formatting(list_text)
                html_parts.append(f'<li>{list_text}</li>')
                continue
            
            if self._is_blockquote(line):
                if current_paragraph:
                    paragraph_text = ' '.join(current_paragraph)
                    paragraph_text = self._process_inline_formatting(paragraph_text)
                    html_parts.append(f'<p>{paragraph_text}</p>')
                    current_paragraph = []
                
                quote_text = self._strip_blockquote_markers(line)
                quote_text = self._process_inline_formatting(quote_text)
                html_parts.append(f'<blockquote>{quote_text}</blockquote>')
                continue
            
            current_paragraph.append(line)
        
        if current_paragraph:
            paragraph_text = ' '.join(current_paragraph)
            paragraph_text = self._process_inline_formatting(paragraph_text)
            html_parts.append(f'<p>{paragraph_text}</p>')
        
        if images:
            html_parts.append('<div class="images-section">')
            for img in images:
                img_ext = self._get_image_extension(img.format)
                img_src = f'images/{img.image_id}.{img_ext}'
                img_html = f'<figure class="image-figure"><img src="{img_src}" alt="{img.image_id}" class="chapter-image"/>'
                if img.width > 0 and img.height > 0:
                    img_html = f'<figure class="image-figure"><img src="{img_src}" alt="{img.image_id}" class="chapter-image" width="{img.width}" height="{img.height}"/>'
                img_html += f'<figcaption class="image-caption">图 {img.image_id}</figcaption></figure>'
                html_parts.append(img_html)
            html_parts.append('</div>')
        
        return self._wrap_html_document('\n'.join(html_parts), title)

    def _get_image_extension(self, img_format: str) -> str:
        format_lower = img_format.lower()
        if format_lower in ['jpeg', 'jpg', 'dct']:
            return 'jpg'
        elif format_lower == 'png':
            return 'png'
        elif format_lower in ['gif', 'jpeg2000', 'jp2', 'tif', 'tiff', 'bmp']:
            return format_lower
        return 'jpg'

    def _is_heading(self, line: str) -> bool:
        if len(line) > 100:
            return False
        
        patterns = [
            r'^\d+\.\d+\.?\s+[A-Z]',
            r'^[A-Z][A-Z\s]{2,50}$',
            r'^(Chapter|Section|第|附录)\s*\d+',
        ]
        
        for pattern in patterns:
            if re.match(pattern, line):
                return True
        
        return False

    def _determine_heading_level(self, line: str) -> int:
        if re.match(r'^\d+\.\d+\.\d+', line):
            return 4
        if re.match(r'^\d+\.\d+', line):
            return 3
        if re.match(r'^\d+\.', line):
            return 2
        return 3

    def _strip_heading_markers(self, line: str) -> str:
        line = re.sub(r'^\d+\.\d+\.\d+\.?\s*', '', line)
        line = re.sub(r'^\d+\.\d+\.?\s*', '', line)
        line = re.sub(r'^\d+\.?\s*', '', line)
        return line.strip()

    def _is_list_item(self, line: str) -> bool:
        return bool(re.match(r'^[\-\*\u2022]\s+', line) or re.match(r'^\d+[\.\)]\s+', line))

    def _strip_list_markers(self, line: str) -> str:
        line = re.sub(r'^[\-\*\u2022]\s+', '', line)
        line = re.sub(r'^\d+[\.\)]\s+', '', line)
        return line.strip()

    def _is_blockquote(self, line: str) -> bool:
        return bool(re.match(r'^["\u201c\u201d]', line) or line.startswith('>'))

    def _strip_blockquote_markers(self, line: str) -> str:
        line = re.sub(r'^>\s*', '', line)
        line = line.strip('"\u201c\u201d')
        return line.strip()

    def _process_inline_formatting(self, text: str) -> str:
        text = html.escape(text)
        
        text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
        text = re.sub(r'__(.+?)__', r'<strong>\1</strong>', text)
        text = re.sub(r'_(.+?)_', r'<em>\1</em>', text)
        
        text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
        
        text = re.sub(r'\[(.+?)\]\((.+?)\)', r'<a href="\2">\1</a>', text)
        
        return text

    def _slugify(self, text: str) -> str:
        text = re.sub(r'[^\w\s-]', '', text).strip().lower()
        text = re.sub(r'[-\s]+', '-', text)
        return text or 'section'

    def _wrap_html_document(self, body_content: str, title: str) -> str:
        soup = BeautifulSoup(features='html.parser')
        
        html_tag = soup.new_tag('html', xmlns='http://www.w3.org/1999/xhtml')
        soup.append(html_tag)
        
        head_tag = soup.new_tag('head')
        html_tag.append(head_tag)
        
        meta_tag = soup.new_tag('meta', **{'http-equiv': 'Content-Type', 'content': 'text/html; charset=utf-8'})
        head_tag.append(meta_tag)
        
        title_tag = soup.new_tag('title')
        title_tag.string = title
        head_tag.append(title_tag)
        
        style_tag = soup.new_tag('style', type='text/css')
        style_tag.string = '''
            body { font-family: serif; line-height: 1.6; margin: 1em; }
            h1, h2, h3, h4, h5, h6 { font-family: sans-serif; margin-top: 1.5em; margin-bottom: 0.5em; }
            p { margin: 0.5em 0; text-indent: 2em; }
            blockquote { margin: 1em 2em; font-style: italic; color: #666; }
            li { margin: 0.25em 0; }
            code { font-family: monospace; background: #f0f0f0; padding: 0.1em 0.3em; }
            .images-section { margin: 2em 0; text-align: center; }
            .image-figure { margin: 1.5em auto; max-width: 100%; }
            .chapter-image { max-width: 100%; height: auto; display: block; margin: 0 auto; border: 1px solid #ddd; }
            .image-caption { margin-top: 0.5em; font-size: 0.9em; color: #666; font-style: italic; }
        '''
        head_tag.append(style_tag)
        
        body_tag = soup.new_tag('body')
        body_tag.append(BeautifulSoup(body_content, 'html.parser'))
        html_tag.append(body_tag)
        
        return str(soup)

    def generate_navigation_html(self, chapters: List[Chapter], book_title: str) -> str:
        soup = BeautifulSoup(features='html.parser')
        
        html_tag = soup.new_tag('html', xmlns='http://www.w3.org/1999/xhtml')
        soup.append(html_tag)
        
        head_tag = soup.new_tag('head')
        html_tag.append(head_tag)
        
        meta_tag = soup.new_tag('meta', **{'http-equiv': 'Content-Type', 'content': 'text/html; charset=utf-8'})
        head_tag.append(meta_tag)
        
        title_tag = soup.new_tag('title')
        title_tag.string = f'{book_title} - 目录'
        head_tag.append(title_tag)
        
        body_tag = soup.new_tag('body')
        html_tag.append(body_tag)
        
        h1_tag = soup.new_tag('h1')
        h1_tag.string = '目录'
        body_tag.append(h1_tag)
        
        self._build_toc_list(soup, body_tag, chapters)
        
        return str(soup)

    def _build_toc_list(self, soup, parent, chapters: List[Chapter], prefix: str = ''):
        ul_tag = soup.new_tag('ul')
        parent.append(ul_tag)
        
        for i, chapter in enumerate(chapters):
            li_tag = soup.new_tag('li')
            ul_tag.append(li_tag)
            
            a_tag = soup.new_tag('a', href=f'chapter_{prefix}{i + 1}.xhtml')
            a_tag.string = chapter.title
            li_tag.append(a_tag)
            
            if chapter.children:
                self._build_toc_list(soup, li_tag, chapter.children, f'{prefix}{i + 1}_')
