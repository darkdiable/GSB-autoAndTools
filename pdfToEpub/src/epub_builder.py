import os
from typing import List

from ebooklib import epub

from .content_processor import ContentProcessor, ChapterContent
from .toc_processor import TOCProcessor, ChapterInfo


class EPUBBuilder:
    def __init__(
        self,
        content_processor: ContentProcessor,
        toc_processor: TOCProcessor,
        book_title: str = "Untitled",
        book_author: str = "Unknown",
        language: str = "zh",
    ):
        self.content_processor = content_processor
        self.toc_processor = toc_processor
        self.book_title = book_title
        self.book_author = book_author
        self.language = language

    def build(self, output_path: str) -> str:
        book = epub.EpubBook()
        book.set_title(self.book_title)
        book.set_language(self.language)
        book.add_author(self.book_author)

        chapter_contents = self.toc_processor.build_chapter_contents()
        toc_items = self.toc_processor.get_toc_items()

        epub_chapters = self._create_chapters(book, chapter_contents)
        self._setup_navigation(book, epub_chapters, toc_items)
        self._add_cover_page(book, epub_chapters)

        epub.write_epub(output_path, book, {})
        return output_path

    def _create_chapters(
        self,
        book: epub.EpubBook,
        chapter_contents: List[ChapterContent],
    ) -> List[epub.EpubHtml]:
        epub_chapters = []

        for content in chapter_contents:
            html_body = self.content_processor.text_to_html_paragraphs(
                content.get_full_text()
            )
            html_content = self._wrap_chapter_html(content.title, html_body)

            chapter = epub.EpubHtml(
                title=content.title,
                file_name=f"{content.chapter_id}.xhtml",
                lang=self.language,
            )
            chapter.content = html_content
            chapter.add_item(
                epub.EpubItem(
                    uid="style_default",
                    file_name="style/default.css",
                    media_type="text/css",
                    content=self._get_default_css().encode("utf-8"),
                )
            )

            book.add_item(chapter)
            epub_chapters.append(chapter)

        return epub_chapters

    def _setup_navigation(
        self,
        book: epub.EpubBook,
        epub_chapters: List[epub.EpubHtml],
        toc_items: list,
    ) -> None:
        toc = []
        for chapter, (title, chapter_id, level) in zip(epub_chapters, toc_items):
            if level == 1:
                section = epub.Section(title)
                nested = []
                toc.append((section, nested))
            else:
                if toc and isinstance(toc[-1], tuple):
                    toc[-1][1].append(chapter)
                else:
                    toc.append(chapter)

        flat_toc = []
        for item in toc:
            if isinstance(item, tuple):
                section, nested = item
                flat_toc.append(section)
                flat_toc.extend(nested)
            else:
                flat_toc.append(item)

        if not flat_toc:
            flat_toc = epub_chapters

        book.toc = flat_toc

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

        style_item = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=self._get_nav_css().encode("utf-8"),
        )
        book.add_item(style_item)

    def _add_cover_page(
        self,
        book: epub.EpubBook,
        epub_chapters: List[epub.EpubHtml],
    ) -> None:
        spine = ["nav"]
        if epub_chapters:
            spine.append(epub_chapters[0])
            spine.extend(epub_chapters[1:])
        book.spine = spine

    @staticmethod
    def _wrap_chapter_html(title: str, body_html: str) -> str:
        return f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>{title}</title>
    <link rel="stylesheet" type="text/css" href="style/default.css"/>
</head>
<body>
    <h1>{title}</h1>
    {body_html}
</body>
</html>"""

    @staticmethod
    def _get_default_css() -> str:
        return """body {
    font-family: serif;
    line-height: 1.8;
    margin: 1em;
    color: #333;
}
h1 {
    font-size: 1.5em;
    text-align: center;
    margin-bottom: 1em;
    color: #222;
    border-bottom: 1px solid #ccc;
    padding-bottom: 0.5em;
}
h2 {
    font-size: 1.3em;
    color: #333;
}
p {
    text-indent: 2em;
    margin: 0.5em 0;
    text-align: justify;
}
"""

    @staticmethod
    def _get_nav_css() -> str:
        return """nav ol {
    list-style-type: none;
    padding-left: 1em;
}
nav li {
    margin: 0.3em 0;
}
nav a {
    color: #0066cc;
    text-decoration: none;
}
nav a:hover {
    text-decoration: underline;
}
"""


def convert_pdf_to_epub(
    pdf_path: str,
    output_dir: str,
    book_title: str = None,
    book_author: str = "Unknown",
    language: str = "zh",
) -> str:
    if book_title is None:
        book_title = os.path.splitext(os.path.basename(pdf_path))[0]

    content_processor = ContentProcessor(pdf_path)
    toc_processor = TOCProcessor(content_processor)
    builder = EPUBBuilder(
        content_processor=content_processor,
        toc_processor=toc_processor,
        book_title=book_title,
        book_author=book_author,
        language=language,
    )

    os.makedirs(output_dir, exist_ok=True)
    epub_filename = f"{book_title}.epub"
    output_path = os.path.join(output_dir, epub_filename)

    return builder.build(output_path)
