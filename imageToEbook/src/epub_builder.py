import os
from typing import Optional

from ebooklib import epub

from . import config
from .image_handler import (
    ImageInfo,
    scan_images,
    get_cover_image,
    get_content_images,
    read_image_data,
    get_image_mime_type,
)

PAGE_STYLE = """
body {
    margin: 0;
    padding: 0;
    -webkit-user-select: text;
    -moz-user-select: text;
    -ms-user-select: text;
    user-select: text;
}
.page-container {
    margin: 0;
    padding: 0;
    text-align: center;
    page-break-after: always;
}
.page-container a {
    text-decoration: none;
    display: block;
}
.page-container img {
    max-width: 100%;
    max-height: 100%;
    width: auto;
    height: auto;
    display: block;
    margin: 0 auto;
    object-fit: contain;
    cursor: pointer;
}
"""

PAGE_ZOOM_STYLE = """
body {
    margin: 0;
    padding: 0;
    background-color: #ffffff;
    -webkit-user-select: text;
    -moz-user-select: text;
    -ms-user-select: text;
    user-select: text;
}
.zoom-container {
    margin: 0;
    padding: 0;
    text-align: center;
}
.zoom-container a {
    text-decoration: none;
    display: inline-block;
    color: #666;
    font-size: 0.9em;
    margin: 10px 0;
}
.zoom-container img {
    max-width: none;
    max-height: none;
    width: auto;
    height: auto;
    display: block;
    margin: 0 auto;
}
"""

COVER_STYLE = """
body {
    margin: 0;
    padding: 0;
}
.cover-container {
    margin: 0;
    padding: 0;
    text-align: center;
}
.cover-container img {
    max-width: 100%;
    max-height: 100%;
    width: 100%;
    height: 100%;
    display: block;
    object-fit: contain;
}
"""


def _create_image_chapter(img: ImageInfo, index: int) -> tuple[epub.EpubHtml, epub.EpubImage]:
    chapter_id = f"page_{index:04d}"
    img_uid = f"img_{index:04d}"
    html_file = f"page_{index:04d}.xhtml"

    data = read_image_data(img)
    mime = get_image_mime_type(img)

    epub_image = epub.EpubImage()
    epub_image.id = img_uid
    epub_image.file_name = f"images/{img.filename}"
    epub_image.media_type = mime
    epub_image.content = data

    html_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>Page {index}</title>
    <link rel="stylesheet" type="text/css" href="style/page.css"/>
</head>
<body>
    <div class="page-container">
        <a href="zoom_{index:04d}.xhtml">
            <img src="images/{img.filename}" alt="{img.basename}" title="点击放大"/>
        </a>
    </div>
</body>
</html>"""

    chapter = epub.EpubHtml(
        uid=chapter_id,
        file_name=html_file,
        title=f"Page {index}",
    )
    chapter.content = html_content.encode("utf-8")

    return chapter, epub_image


def _create_zoom_chapter(img: ImageInfo, index: int) -> epub.EpubHtml:
    chapter_id = f"zoom_{index:04d}"
    html_file = f"zoom_{index:04d}.xhtml"

    html_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>Zoom Page {index}</title>
    <link rel="stylesheet" type="text/css" href="style/zoom.css"/>
</head>
<body>
    <div class="zoom-container">
        <a href="page_{index:04d}.xhtml">[ 返回页面 {index} ]</a>
        <img src="images/{img.filename}" alt="{img.basename}"/>
        <a href="page_{index:04d}.xhtml">[ 返回页面 {index} ]</a>
    </div>
</body>
</html>"""

    chapter = epub.EpubHtml(
        uid=chapter_id,
        file_name=html_file,
        title=f"Zoom Page {index}",
    )
    chapter.content = html_content.encode("utf-8")

    return chapter


def _create_cover_chapter(cover_img: ImageInfo) -> epub.EpubHtml:
    data = read_image_data(cover_img)
    mime = get_image_mime_type(cover_img)

    epub_image = epub.EpubImage()
    epub_image.id = "cover-image"
    epub_image.file_name = f"images/{cover_img.filename}"
    epub_image.media_type = mime
    epub_image.content = data

    html_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
    <title>Cover</title>
    <link rel="stylesheet" type="text/css" href="style/cover.css"/>
</head>
<body>
    <div class="cover-container">
        <img src="images/{cover_img.filename}" alt="Cover"/>
    </div>
</body>
</html>"""

    chapter = epub.EpubHtml(
        uid="cover-page",
        file_name="cover.xhtml",
        title="Cover",
    )
    chapter.content = html_content.encode("utf-8")
    chapter.add_item(epub_image)

    return chapter, epub_image


def build_epub(
    title: Optional[str] = None,
    author: Optional[str] = None,
    language: Optional[str] = None,
    output_name: Optional[str] = None,
) -> str:
    title = title or config.BOOK_TITLE
    author = author or config.BOOK_AUTHOR
    language = language or config.BOOK_LANGUAGE
    output_name = output_name or config.EPUB_OUTPUT_NAME

    images = scan_images()
    if not images:
        raise ValueError("No images found in the image directory.")

    book = epub.EpubBook()
    book.set_identifier("image-ebook-gen")
    book.set_title(title)
    book.set_language(language)
    book.add_author(author)

    page_css = epub.EpubItem(
        uid="page-style",
        file_name="style/page.css",
        media_type="text/css",
        content=PAGE_STYLE.encode("utf-8"),
    )
    cover_css = epub.EpubItem(
        uid="cover-style",
        file_name="style/cover.css",
        media_type="text/css",
        content=COVER_STYLE.encode("utf-8"),
    )
    zoom_css = epub.EpubItem(
        uid="zoom-style",
        file_name="style/zoom.css",
        media_type="text/css",
        content=PAGE_ZOOM_STYLE.encode("utf-8"),
    )
    book.add_item(page_css)
    book.add_item(cover_css)
    book.add_item(zoom_css)

    spine = []
    toc = []

    cover_img = get_cover_image(images)
    if cover_img:
        cover_chapter, cover_epub_image = _create_cover_chapter(cover_img)
        cover_chapter.add_item(cover_css)
        book.add_item(cover_epub_image)
        book.add_item(cover_chapter)

        book.add_metadata(None, "meta", "", {"name": "cover", "content": cover_epub_image.id})

        spine.append(cover_chapter)

    content_images = get_content_images(images)
    for idx, img in enumerate(content_images, start=1):
        chapter, epub_image = _create_image_chapter(img, idx)
        chapter.add_item(page_css)
        book.add_item(epub_image)
        book.add_item(chapter)

        zoom_chapter = _create_zoom_chapter(img, idx)
        zoom_chapter.add_item(zoom_css)
        book.add_item(zoom_chapter)

        spine.append(chapter)
        toc.append(chapter)

    book.toc = toc
    book.spine = spine

    nav = epub.EpubNav()
    book.add_item(nav)

    ncx = epub.EpubNcx()
    book.add_item(ncx)

    book.add_metadata("http://www.idpf.org/2007/opf", "meta", "pre-paginated", {"property": "rendition:layout"})
    book.add_metadata("http://www.idpf.org/2007/opf", "meta", "auto", {"property": "rendition:orientation"})
    book.add_metadata("http://www.idpf.org/2007/opf", "meta", "auto", {"property": "rendition:spread"})

    os.makedirs(config.EPUB_DIR, exist_ok=True)
    output_path = os.path.join(config.EPUB_DIR, output_name)
    epub.write_epub(output_path, book)
    return output_path
