import os
from typing import List, Dict, Tuple, Optional
from ebooklib import epub
from bs4 import BeautifulSoup

from .toc_extractor import Chapter
from .content_processor import ChapterContent
from .pdf_parser import PdfImage


class EpubGenerator:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def generate(self, 
                 book_title: str, 
                 chapters: List[Chapter], 
                 chapter_contents: List[ChapterContent],
                 metadata: Optional[Dict] = None,
                 output_filename: Optional[str] = None) -> str:
        if not output_filename:
            output_filename = f"{self._sanitize_filename(book_title)}.epub"
        
        output_path = os.path.join(self.output_dir, output_filename)
        
        book = epub.EpubBook()
        
        book.set_identifier(f'pdf2epub_{book_title}_{os.urandom(4).hex()}')
        book.set_title(book_title)
        book.set_language('zh-CN')
        
        if metadata:
            if metadata.get('author'):
                book.add_author(metadata['author'])
            if metadata.get('subject'):
                book.add_metadata('DC', 'subject', metadata['subject'])
            if metadata.get('creator'):
                book.add_metadata('DC', 'creator', metadata['creator'])
        
        nav_html = self._create_navigation_page(chapters, book_title)
        nav_page = epub.EpubHtml(
            title='目录',
            file_name='toc.xhtml',
            content=nav_html
        )
        book.add_item(nav_page)
        
        epub_chapters = []
        self._add_chapters_to_book(book, chapters, chapter_contents, epub_chapters, prefix='')
        
        book.toc = tuple(epub_chapters)
        
        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())
        
        style = '''
            @namespace epub "http://www.idpf.org/2007/ops";
            body { font-family: serif; line-height: 1.6; margin: 1em; }
            h1, h2, h3, h4, h5, h6 { font-family: sans-serif; margin-top: 1.5em; margin-bottom: 0.5em; }
            p { margin: 0.5em 0; text-indent: 2em; }
            blockquote { margin: 1em 2em; font-style: italic; color: #666; }
            li { margin: 0.25em 0; }
            code { font-family: monospace; background: #f0f0f0; padding: 0.1em 0.3em; }
            .toc { list-style: none; padding-left: 1em; }
            .toc li { margin: 0.3em 0; }
            .toc a { text-decoration: none; color: inherit; }
            .toc a:hover { text-decoration: underline; }
        '''
        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=style
        )
        book.add_item(nav_css)
        
        all_images = self._collect_all_images(chapter_contents)
        self._add_images_to_book(book, all_images)
        
        spine = [nav_page]
        for content in chapter_contents:
            for item in book.get_items():
                if isinstance(item, epub.EpubHtml) and item.file_name == f'{content.chapter_id}.xhtml':
                    spine.append(item)
                    break
        book.spine = spine
        
        epub.write_epub(output_path, book, {})
        
        return output_path

    def _add_chapters_to_book(self, book, chapters: List[Chapter], 
                              chapter_contents: List[ChapterContent], 
                              epub_chapters: List, prefix: str = ''):
        content_map = {c.chapter_id: c for c in chapter_contents}
        
        for i, chapter in enumerate(chapters):
            chapter_id = f'chapter_{prefix}{i + 1}'
            content = content_map.get(chapter_id)
            
            if content:
                epub_chapter = self._create_epub_chapter(content)
                book.add_item(epub_chapter)
                epub_chapters.append(epub_chapter)
                
                if chapter.children:
                    child_epub_chapters = []
                    self._add_chapters_to_book(
                        book, chapter.children, chapter_contents, 
                        child_epub_chapters, f'{prefix}{i + 1}_'
                    )
                    if child_epub_chapters:
                        epub_chapters.append(tuple(child_epub_chapters))
            else:
                if chapter.children:
                    child_epub_chapters = []
                    self._add_chapters_to_book(
                        book, chapter.children, chapter_contents, 
                        child_epub_chapters, f'{prefix}{i + 1}_'
                    )
                    if child_epub_chapters:
                        epub_chapters.extend(child_epub_chapters)

    def _create_epub_chapter(self, content: ChapterContent) -> epub.EpubHtml:
        chapter = epub.EpubHtml(
            title=content.title,
            file_name=f'{content.chapter_id}.xhtml',
            content=content.html_content
        )
        return chapter

    def _create_navigation_page(self, chapters: List[Chapter], book_title: str) -> str:
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
        
        link_tag = soup.new_tag('link', rel='stylesheet', href='style/nav.css', type='text/css')
        head_tag.append(link_tag)
        
        body_tag = soup.new_tag('body')
        html_tag.append(body_tag)
        
        h1_tag = soup.new_tag('h1')
        h1_tag.string = '目录'
        body_tag.append(h1_tag)
        
        self._build_toc_html(soup, body_tag, chapters)
        
        return str(soup)

    def _build_toc_html(self, soup, parent, chapters: List[Chapter], prefix: str = ''):
        ul_tag = soup.new_tag('ul', **{'class': 'toc'})
        parent.append(ul_tag)
        
        for i, chapter in enumerate(chapters):
            li_tag = soup.new_tag('li')
            ul_tag.append(li_tag)
            
            chapter_id = f'chapter_{prefix}{i + 1}'
            a_tag = soup.new_tag('a', href=f'{chapter_id}.xhtml')
            a_tag.string = chapter.title
            li_tag.append(a_tag)
            
            if chapter.children:
                self._build_toc_html(soup, li_tag, chapter.children, f'{prefix}{i + 1}_')

    def _sanitize_filename(self, filename: str) -> str:
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename.strip()

    def _collect_all_images(self, chapter_contents: List[ChapterContent]) -> List[PdfImage]:
        all_images = []
        seen_ids = set()
        
        for content in chapter_contents:
            if content.images:
                for img in content.images:
                    if img.image_id not in seen_ids:
                        seen_ids.add(img.image_id)
                        all_images.append(img)
        
        return all_images

    def _add_images_to_book(self, book, images: List[PdfImage]):
        for img in images:
            try:
                img_ext = self._get_image_extension(img.format)
                media_type = self._get_media_type(img.format)
                
                epub_image = epub.EpubItem(
                    uid=img.image_id,
                    file_name=f'images/{img.image_id}.{img_ext}',
                    media_type=media_type,
                    content=img.data
                )
                book.add_item(epub_image)
            except Exception as e:
                print(f"  添加图片 {img.image_id} 时出错: {e}")

    def _get_image_extension(self, img_format: str) -> str:
        format_lower = img_format.lower()
        if format_lower in ['jpeg', 'jpg', 'dct', 'jpeg2000', 'jp2', 'tif', 'tiff', 'bmp', 'gif']:
            return 'jpg'
        elif format_lower == 'png':
            return 'png'
        return 'jpg'

    def _get_media_type(self, img_format: str) -> str:
        format_lower = img_format.lower()
        if format_lower in ['jpeg', 'jpg', 'dct', 'jpeg2000', 'jp2', 'tif', 'tiff', 'bmp', 'gif']:
            return 'image/jpeg'
        elif format_lower == 'png':
            return 'image/png'
        return 'image/jpeg'
