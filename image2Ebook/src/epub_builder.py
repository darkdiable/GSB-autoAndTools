import os
import zipfile
import shutil
import uuid
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timezone


class EpubBuilder:
    def __init__(self, output_dir: str, book_title: str = "图片电子书", author: str = "Unknown"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.book_title = book_title
        self.author = author
        self.book_id = str(uuid.uuid4())
        self.temp_dir = self.output_dir / f"_temp_{self.book_id}"
        self.epub_dir = self.temp_dir / "EPUB"
        self.meta_inf_dir = self.temp_dir / "META-INF"

    def _create_directory_structure(self):
        self.temp_dir.mkdir(parents=True, exist_ok=True)
        self.epub_dir.mkdir(parents=True, exist_ok=True)
        self.meta_inf_dir.mkdir(parents=True, exist_ok=True)
        (self.epub_dir / "images").mkdir(parents=True, exist_ok=True)
        (self.epub_dir / "text").mkdir(parents=True, exist_ok=True)
        (self.epub_dir / "style").mkdir(parents=True, exist_ok=True)

    def _write_mimetype(self):
        mimetype_path = self.temp_dir / "mimetype"
        with open(mimetype_path, 'w', encoding='utf-8') as f:
            f.write("application/epub+zip")

    def _write_container_xml(self):
        container_content = '''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="EPUB/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>'''
        with open(self.meta_inf_dir / "container.xml", 'w', encoding='utf-8') as f:
            f.write(container_content)

    def _write_css(self):
        css_content = '''@page {
  margin: 0;
  padding: 0;
}

body {
  margin: 0;
  padding: 0;
  background-color: #FFFFFF;
}

img {
  display: block;
  margin: 0 auto;
  padding: 0;
  max-width: 100%;
  max-height: 100%;
}

.page {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
  page-break-after: always;
}
'''
        with open(self.epub_dir / "style" / "main.css", 'w', encoding='utf-8') as f:
            f.write(css_content)

    def _write_xhtml_page(self, page_name: str, image_path: str, is_cover: bool = False):
        xhtml_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head>
  <title>{self.book_title}</title>
  <meta charset="UTF-8"/>
  <link rel="stylesheet" type="text/css" href="../style/main.css"/>
</head>
<body>
  <div class="page" {'epub:type="cover"' if is_cover else ''}>
    <img src="../images/{os.path.basename(image_path)}" alt="{'Cover' if is_cover else 'Page'}"/>
  </div>
</body>
</html>'''
        with open(self.epub_dir / "text" / page_name, 'w', encoding='utf-8') as f:
            f.write(xhtml_content)

    def _write_content_opf(self, cover_image: Optional[str], content_images: List[str]):
        modified_date = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        manifest_items = []
        spine_items = []
        
        manifest_items.append('<item id="style" href="style/main.css" media-type="text/css"/>')
        
        if cover_image:
            manifest_items.append(f'<item id="cover-image" href="images/{os.path.basename(cover_image)}" media-type="image/{self._get_image_type(cover_image)}" properties="cover-image"/>')
            manifest_items.append('<item id="cover" href="text/cover.xhtml" media-type="application/xhtml+xml"/>')
            spine_items.append('<itemref idref="cover"/>')
        
        for i, img in enumerate(content_images):
            page_id = f"page{i+1:04d}"
            img_id = f"img{i+1:04d}"
            manifest_items.append(f'<item id="{img_id}" href="images/{os.path.basename(img)}" media-type="image/{self._get_image_type(img)}"/>')
            manifest_items.append(f'<item id="{page_id}" href="text/{page_id}.xhtml" media-type="application/xhtml+xml"/>')
            spine_items.append(f'<itemref idref="{page_id}"/>')
        
        manifest_str = '\n    '.join(manifest_items)
        spine_str = '\n    '.join(spine_items)
        
        opf_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookId">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="BookId">{self.book_id}</dc:identifier>
    <dc:title>{self.book_title}</dc:title>
    <dc:creator>{self.author}</dc:creator>
    <dc:language>zh-CN</dc:language>
    <meta property="dcterms:modified">{modified_date}</meta>
  </metadata>
  <manifest>
    {manifest_str}
  </manifest>
  <spine>
    {spine_str}
  </spine>
</package>'''
        with open(self.epub_dir / "content.opf", 'w', encoding='utf-8') as f:
            f.write(opf_content)

    def _get_image_type(self, filename: str) -> str:
        ext = os.path.splitext(filename)[1].lower()
        type_map = {
            '.png': 'png',
            '.jpg': 'jpeg',
            '.jpeg': 'jpeg',
            '.gif': 'gif',
            '.bmp': 'bmp',
            '.webp': 'webp'
        }
        return type_map.get(ext, 'jpeg')

    def _copy_images(self, cover_image: Optional[str], content_images: List[str], img_dir: str):
        images_dir = self.epub_dir / "images"
        if cover_image:
            src = Path(img_dir) / cover_image
            dst = images_dir / os.path.basename(cover_image)
            shutil.copy2(src, dst)
        
        for img in content_images:
            src = Path(img_dir) / img
            dst = images_dir / os.path.basename(img)
            shutil.copy2(src, dst)

    def _create_xhtml_pages(self, cover_image: Optional[str], content_images: List[str]):
        if cover_image:
            self._write_xhtml_page("cover.xhtml", cover_image, is_cover=True)
        
        for i, img in enumerate(content_images):
            page_name = f"page{i+1:04d}.xhtml"
            self._write_xhtml_page(page_name, img, is_cover=False)

    def _create_epub_zip(self, output_filename: str) -> str:
        epub_path = self.output_dir / output_filename
        if epub_path.exists():
            epub_path.unlink()
        
        with zipfile.ZipFile(epub_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.write(self.temp_dir / "mimetype", "mimetype", compress_type=zipfile.ZIP_STORED)
            
            for root, dirs, files in os.walk(self.temp_dir):
                for file in files:
                    if file == "mimetype":
                        continue
                    file_path = Path(root) / file
                    arcname = str(file_path.relative_to(self.temp_dir))
                    zf.write(file_path, arcname)
        
        return str(epub_path)

    def _cleanup_temp(self):
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)

    def build(self, img_dir: str, cover_image: Optional[str], content_images: List[str], output_filename: str = "output.epub") -> str:
        try:
            self._create_directory_structure()
            self._write_mimetype()
            self._write_container_xml()
            self._write_css()
            self._copy_images(cover_image, content_images, img_dir)
            self._create_xhtml_pages(cover_image, content_images)
            self._write_content_opf(cover_image, content_images)
            epub_path = self._create_epub_zip(output_filename)
            return epub_path
        finally:
            self._cleanup_temp()
