import os
from typing import Dict, List

from ebooklib import epub

from .content_processor import ContentProcessor, ChapterContent, ImageContent
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
        self._image_map: Dict[str, ImageContent] = {}

    def build(self, output_path: str) -> str:
        book = epub.EpubBook()
        book.set_identifier("book_" + str(hash(self.book_title))[:8])
        book.set_title(self.book_title)
        book.set_language(self.language)
        book.add_author(self.book_author)

        self._add_styles(book)
        self._add_images(book)

        chapter_contents = self.toc_processor.build_chapter_contents()
        toc_items = self.toc_processor.get_toc_items()

        epub_chapters = self._create_chapters(book, chapter_contents)
        self._setup_navigation(book, epub_chapters, toc_items)
        self._setup_spine(book, epub_chapters)

        epub.write_epub(output_path, book, {})
        return output_path

    def _add_styles(self, book: epub.EpubBook) -> None:
        default_css = epub.EpubItem(
            uid="style_default",
            file_name="style/default.css",
            media_type="text/css",
            content=self._get_default_css().encode("utf-8"),
        )
        book.add_item(default_css)

        nav_css = epub.EpubItem(
            uid="style_nav",
            file_name="style/nav.css",
            media_type="text/css",
            content=self._get_nav_css().encode("utf-8"),
        )
        book.add_item(nav_css)

    def _add_images(self, book: epub.EpubBook) -> None:
        all_images = self.content_processor.get_all_images()
        for img in all_images:
            media_type = self._get_media_type(img.format)
            epub_img = epub.EpubItem(
                uid=img.image_id,
                file_name=img.file_name,
                media_type=media_type,
                content=img.image_data,
            )
            book.add_item(epub_img)
            self._image_map[img.image_id] = img

    @staticmethod
    def _get_media_type(img_format: str) -> str:
        mapping = {
            "png": "image/png",
            "jpeg": "image/jpeg",
            "jpg": "image/jpeg",
            "gif": "image/gif",
            "bmp": "image/bmp",
            "svg": "image/svg+xml",
        }
        return mapping.get(img_format, "image/png")

    def _create_chapters(
        self,
        book: epub.EpubBook,
        chapter_contents: List[ChapterContent],
    ) -> List[epub.EpubHtml]:
        epub_chapters = []

        for content in chapter_contents:
            html_body = self._build_chapter_html_body(content)
            escaped_title = self.content_processor.html_escape(content.title)
            html_content = self._wrap_chapter_html(escaped_title, html_body)

            chapter = epub.EpubHtml(
                title=content.title,
                file_name=f"{content.chapter_id}.xhtml",
                lang=self.language,
            )
            chapter.content = html_content

            book.add_item(chapter)
            epub_chapters.append(chapter)

        return epub_chapters

    def _build_chapter_html_body(self, content: ChapterContent) -> str:
        elements = content.get_elements()
        if elements:
            return self.content_processor.elements_to_html(elements)

        text = content.get_full_text()
        if text.strip():
            return self.content_processor.text_to_html_paragraphs(text)

        return ""

    def _setup_navigation(
        self,
        book: epub.EpubBook,
        epub_chapters: List[epub.EpubHtml],
        toc_items: list,
    ) -> None:
        book.toc = tuple(epub_chapters)

        book.add_item(epub.EpubNcx())
        book.add_item(epub.EpubNav())

    def _setup_spine(
        self,
        book: epub.EpubBook,
        epub_chapters: List[epub.EpubHtml],
    ) -> None:
        spine = ["nav"]
        spine.extend(epub_chapters)
        book.spine = spine

    @staticmethod
    def _wrap_chapter_html(title: str, body_html: str) -> str:
        return f"""<html>
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
        return """@namespace epub "http://www.idpf.org/2007/ops";
body {
    font-family: Georgia, serif;
    line-height: 1.8;
    margin: 1em;
    color: #333;
}
h1 {
    font-size: 1.5em;
    text-align: center;
    margin: 1em 0;
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
.image-container {
    text-align: center;
    margin: 1em 0;
}
.chapter-image {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 0 auto;
    page-break-inside: avoid;
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
