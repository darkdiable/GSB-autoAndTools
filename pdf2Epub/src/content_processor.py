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
        
        body_font_size = self._find_body_font_size(text_blocks)
        current_paragraph_blocks = []
        
        for i, item in enumerate(items):
            if isinstance(item, PdfImage):
                if current_paragraph_blocks:
                    html_parts.append(self._render_paragraph(current_paragraph_blocks))
                    current_paragraph_blocks = []
                
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
                    if current_paragraph_blocks:
                        html_parts.append(self._render_paragraph(current_paragraph_blocks))
                        current_paragraph_blocks = []
                    continue
                
                if self._is_heading_block(item, body_font_size):
                    if current_paragraph_blocks:
                        html_parts.append(self._render_paragraph(current_paragraph_blocks))
                        current_paragraph_blocks = []
                    
                    heading_level = self._determine_heading_block_level(item, body_font_size)
                    heading_text = item.text.strip()
                    html_parts.append(f'<h{heading_level} id="{self._slugify(heading_text)}">{html.escape(heading_text)}</h{heading_level}>')
                    continue
                
                if self._is_list_item(line):
                    if current_paragraph_blocks:
                        html_parts.append(self._render_paragraph(current_paragraph_blocks))
                        current_paragraph_blocks = []
                    
                    list_text = self._strip_list_markers(line)
                    list_text = self._process_inline_formatting(list_text)
                    html_parts.append(f'<li>{list_text}</li>')
                    continue
                
                if self._is_blockquote(line):
                    if current_paragraph_blocks:
                        html_parts.append(self._render_paragraph(current_paragraph_blocks))
                        current_paragraph_blocks = []
                    
                    quote_text = self._strip_blockquote_markers(line)
                    quote_text = self._process_inline_formatting(quote_text)
                    html_parts.append(f'<blockquote>{quote_text}</blockquote>')
                    continue
                
                if current_paragraph_blocks:
                    prev_block = current_paragraph_blocks[-1]
                    if self._should_start_new_paragraph(prev_block, item, body_font_size):
                        html_parts.append(self._render_paragraph(current_paragraph_blocks))
                        current_paragraph_blocks = []
                
                current_paragraph_blocks.append(item)
        
        if current_paragraph_blocks:
            html_parts.append(self._render_paragraph(current_paragraph_blocks))
        
        return self._wrap_html_document('\n'.join(html_parts), title)

    def _find_body_font_size(self, text_blocks: List[TextBlock]) -> float:
        font_size_counts = {}
        for block in text_blocks:
            if block.font_size > 0:
                rounded_size = round(block.font_size, 1)
                font_size_counts[rounded_size] = font_size_counts.get(rounded_size, 0) + 1
        
        if font_size_counts:
            return max(font_size_counts.items(), key=lambda x: x[1])[0]
        return 10.0
    
    def _is_heading_block(self, block: TextBlock, body_font_size: float) -> bool:
        if block.is_heading:
            return True
        
        if block.font_size > body_font_size * 1.15:
            return True
        
        if block.is_bold and block.font_size >= body_font_size * 1.05 and len(block.text.strip()) < 100:
            return True
        
        if self._is_heading(block.text):
            return True
        
        return False
    
    def _determine_heading_block_level(self, block: TextBlock, body_font_size: float) -> int:
        if block.heading_level and block.heading_level > 0:
            return min(block.heading_level, 6)
        
        if block.font_size > body_font_size * 1.5:
            return 2
        elif block.font_size > body_font_size * 1.3:
            return 3
        elif block.font_size > body_font_size * 1.15:
            return 4
        
        return self._determine_heading_level(block.text)
    
    def _should_start_new_paragraph(self, prev_block: TextBlock, curr_block: TextBlock, body_font_size: float) -> bool:
        if curr_block.page_idx != prev_block.page_idx:
            return True
        
        line_gap = curr_block.y0 - prev_block.y1
        if line_gap > body_font_size * 0.8:
            return True
        
        if curr_block.indent_level > prev_block.indent_level:
            return True
        
        if curr_block.is_bold and not prev_block.is_bold and len(curr_block.text.strip()) < 100:
            return True
        
        prev_text = prev_block.text.strip()
        curr_text = curr_block.text.strip()
        
        if prev_text and prev_text[-1] in '.!?。！？':
            if curr_text and curr_text[0].isupper() or (curr_text and '\u4e00' <= curr_text[0] <= '\u9fff'):
                if line_gap > body_font_size * 0.3:
                    return True
        
        return False
    
    def _render_paragraph(self, blocks: List[TextBlock]) -> str:
        if not blocks:
            return ''
        
        text_parts = []
        for block in blocks:
            text = block.text.strip()
            if not text:
                continue
            
            if block.is_bold and block.is_italic:
                text = f'**_{text}_**'
            elif block.is_bold:
                text = f'**{text}**'
            elif block.is_italic:
                text = f'_{text}_'
            
            text_parts.append(text)
        
        paragraph_text = ' '.join(text_parts)
        paragraph_text = self._process_inline_formatting(paragraph_text)
        
        first_block = blocks[0]
        indent_style = ''
        if first_block.indent_level > 0:
            indent = first_block.indent_level * 2
            indent_style = f' style="margin-left: {indent}em;"'
        
        return f'<p{indent_style}>{paragraph_text}</p>'
    
    def _merge_text_and_images(self, text_blocks: List[TextBlock], images: List[PdfImage]) -> List[Union[TextBlock, PdfImage]]:
        all_items = []
        
        for block in text_blocks:
            all_items.append(block)
        
        for img in images:
            all_items.append(img)
        
        def get_sort_key(item):
            if isinstance(item, PdfImage):
                page_idx = item.page_idx
                y_top = item.page_height - item.y1 if item.page_height > 0 else item.y0
                x_left = item.x0
                return (page_idx, y_top, x_left, 1)
            else:
                page_idx = item.page_idx
                y_top = item.y0
                x_left = item.x0
                return (page_idx, y_top, x_left, 0)
        
        all_items.sort(key=get_sort_key)
        
        return all_items

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
        if format_lower in ['jpeg', 'jpg', 'dct', 'jpeg2000', 'jp2', 'tif', 'tiff', 'bmp', 'gif']:
            return 'jpg'
        elif format_lower == 'png':
            return 'png'
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
            @page { margin: 0.5em; }
            body { font-family: "Georgia", "Times New Roman", serif; line-height: 1.8; margin: 0; padding: 1em; text-align: justify; }
            h1, h2, h3, h4, h5, h6 { 
                font-family: "Helvetica", "Arial", sans-serif; 
                font-weight: bold;
                page-break-after: avoid;
                page-break-inside: avoid;
            }
            h1 { font-size: 2.0em; margin-top: 1.5em; margin-bottom: 0.8em; line-height: 1.3; }
            h2 { font-size: 1.6em; margin-top: 1.3em; margin-bottom: 0.7em; line-height: 1.3; }
            h3 { font-size: 1.3em; margin-top: 1.1em; margin-bottom: 0.6em; line-height: 1.3; }
            h4 { font-size: 1.15em; margin-top: 1.0em; margin-bottom: 0.5em; line-height: 1.3; }
            h5 { font-size: 1.05em; margin-top: 0.9em; margin-bottom: 0.4em; line-height: 1.3; }
            h6 { font-size: 1.0em; margin-top: 0.8em; margin-bottom: 0.4em; line-height: 1.3; }
            p { margin: 0.6em 0; text-indent: 2em; orphans: 2; widows: 2; }
            p:first-of-type { text-indent: 0; }
            strong { font-weight: bold; }
            em { font-style: italic; }
            blockquote { 
                margin: 1.2em 2em; 
                padding: 0.5em 1em;
                font-style: italic; 
                color: #555; 
                border-left: 3px solid #ccc;
                background: #f9f9f9;
            }
            ul, ol { margin: 0.8em 0; padding-left: 2em; }
            li { margin: 0.4em 0; }
            code { 
                font-family: "Courier New", Courier, monospace; 
                background: #f5f5f5; 
                padding: 0.15em 0.4em; 
                border-radius: 3px;
                font-size: 0.95em;
            }
            pre { 
                font-family: "Courier New", Courier, monospace; 
                background: #f5f5f5; 
                padding: 1em; 
                overflow-x: auto;
                border-radius: 5px;
            }
            .images-section { margin: 2em 0; text-align: center; }
            .image-figure { 
                margin: 1.5em auto; 
                max-width: 100%; 
                text-align: center;
                page-break-inside: avoid;
            }
            .chapter-image { 
                max-width: 100%; 
                height: auto; 
                display: block; 
                margin: 0 auto; 
                border: 1px solid #ddd;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
            .image-caption { 
                margin-top: 0.6em; 
                font-size: 0.9em; 
                color: #666; 
                font-style: italic;
                text-align: center;
            }
            hr { border: none; border-top: 1px solid #ddd; margin: 2em 0; }
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
