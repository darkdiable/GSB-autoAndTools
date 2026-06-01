import io
import re
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import pdfplumber
from PIL import Image


@dataclass
class ImageContent:
    image_id: str
    page_number: int
    x: float
    y: float
    width: float
    height: float
    image_data: bytes
    format: str = "png"

    @property
    def file_name(self) -> str:
        return f"images/{self.image_id}.{self.format}"


@dataclass
class PageContent:
    page_number: int
    text: str
    lines: List[str] = field(default_factory=list)
    images: List[ImageContent] = field(default_factory=list)


@dataclass
class ChapterContent:
    title: str
    chapter_id: str
    pages: List[PageContent] = field(default_factory=list)
    text: str = ""

    def get_full_text(self) -> str:
        if self.text:
            return self.text
        parts = []
        for page in self.pages:
            if page.text.strip():
                parts.append(page.text.strip())
        return "\n\n".join(parts)

    def get_images(self) -> List[ImageContent]:
        images = []
        for page in self.pages:
            images.extend(page.images)
        return images


class ContentProcessor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self._pages: List[PageContent] = []
        self._image_counter = 0

    def extract_all_pages(self) -> List[PageContent]:
        if self._pages:
            return self._pages

        with pdfplumber.open(self.pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                lines = text.split("\n") if text else []
                images = self._extract_images(page, i + 1)

                page_content = PageContent(
                    page_number=i + 1,
                    text=text,
                    lines=lines,
                    images=images,
                )
                self._pages.append(page_content)

        return self._pages

    def _extract_images(self, page: pdfplumber.page.Page, page_number: int) -> List[ImageContent]:
        images = []
        try:
            for img in page.images:
                self._image_counter += 1
                image_id = f"img_{page_number}_{self._image_counter}"
                try:
                    x0 = float(img.get("x0", 0))
                    y0 = float(img.get("y0", 0))
                    x1 = float(img.get("x1", 0))
                    y1 = float(img.get("y1", 0))
                    width = x1 - x0
                    height = y1 - y0

                    if "stream" in img:
                        raw_data = img["stream"].get_data()
                        img_format = self._detect_image_format(raw_data)
                        if img_format:
                            image_data = raw_data
                        else:
                            image_data = self._convert_to_png(raw_data)
                            img_format = "png"
                    else:
                        bbox = (x0, page.height - y1, x1, page.height - y0)
                        cropped = page.crop(bbox)
                        pil_image = cropped.to_image().original
                        img_format = "png"
                        buffer = io.BytesIO()
                        pil_image.save(buffer, format=img_format)
                        image_data = buffer.getvalue()

                    images.append(ImageContent(
                        image_id=image_id,
                        page_number=page_number,
                        x=x0,
                        y=y0,
                        width=width,
                        height=height,
                        image_data=image_data,
                        format=img_format,
                    ))
                except Exception as e:
                    print(f"Warning: Could not extract image {image_id}: {e}")
                    continue
        except Exception as e:
            print(f"Warning: Could not extract images from page {page_number}: {e}")
        return images

    @staticmethod
    def _detect_image_format(data: bytes) -> Optional[str]:
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "png"
        if data.startswith(b"\xff\xd8\xff"):
            return "jpeg"
        if data.startswith(b"BM"):
            return "bmp"
        if data.startswith(b"GIF87a") or data.startswith(b"GIF89a"):
            return "gif"
        return None

    @staticmethod
    def _convert_to_png(raw_data: bytes) -> bytes:
        try:
            buffer = io.BytesIO(raw_data)
            img = Image.open(buffer)
            output_buffer = io.BytesIO()
            img.convert("RGB").save(output_buffer, format="PNG")
            return output_buffer.getvalue()
        except Exception:
            return raw_data

    def get_page(self, page_number: int) -> PageContent:
        pages = self.extract_all_pages()
        idx = page_number - 1
        if 0 <= idx < len(pages):
            return pages[idx]
        raise IndexError(f"Page {page_number} out of range (1-{len(pages)})")

    def get_page_count(self) -> int:
        pages = self.extract_all_pages()
        return len(pages)

    @staticmethod
    def sanitize_text(text: str) -> str:
        text = re.sub(r"\s+", " ", text)
        text = re.sub(r"\n{3,}", "\n\n", text)
        return text.strip()

    @staticmethod
    def html_escape(text: str) -> str:
        text = text.replace("&", "&amp;")
        text = text.replace("<", "&lt;")
        text = text.replace(">", "&gt;")
        text = text.replace('"', "&quot;")
        return text

    def text_to_html_paragraphs(self, text: str) -> str:
        paragraphs = re.split(r"\n\s*\n", text)
        html_parts = []
        for para in paragraphs:
            para = para.strip()
            if not para:
                continue
            escaped = self.html_escape(para)
            escaped = escaped.replace("\n", "<br/>")
            html_parts.append(f"<p>{escaped}</p>")
        return "\n".join(html_parts)

    def get_all_images(self) -> List[ImageContent]:
        pages = self.extract_all_pages()
        all_images = []
        for page in pages:
            all_images.extend(page.images)
        return all_images
