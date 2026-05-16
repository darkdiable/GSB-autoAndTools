import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup
import html

from .toc_extractor import Chapter


@dataclass
class ChapterContent:
    chapter_id: str
    title: str
    html_content: str
    level: int
    order: int


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
        
        raw_text = pdf_parser.extract_page_range_text(
            chapter.content_start_page,
            chapter.content_end_page
        )
        
        if not raw_text.strip():
            return None
        
        html_content = self._text_to_html(raw_text, chapter.title, chapter.level)
        
        return ChapterContent(
            chapter_id=chapter_id,
            title=chapter.title,
            html_content=html_content,
            level=chapter.level,
            order=order
        )

    def _text_to_html(self, text: str, title: str, level: int) -> str:
        lines = text.split('\n')
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
        
        return self._wrap_html_document('\n'.join(html_parts), title)

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
