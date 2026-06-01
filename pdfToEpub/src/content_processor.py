import io
import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional

import pdfplumber
from PIL import Image


@dataclass
class ImageContent:
    image_id: str
    page_number: int
    top: float
    bottom: float
    image_data: bytes
    format: str = "png"

    @property
    def file_name(self) -> str:
        return f"images/{self.image_id}.{self.format}"


@dataclass
class TextBlock:
    top: float
    bottom: float
    text: str


@dataclass
class ContentElement:
    element_type: str
    top: float
    bottom: float
    text: str = ""
    image: Optional[ImageContent] = None


@dataclass
class PageContent:
    page_number: int
    text: str
    lines: List[str] = field(default_factory=list)
    images: List[ImageContent] = field(default_factory=list)
    elements: List[ContentElement] = field(default_factory=list)


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

    def get_elements(self) -> List[ContentElement]:
        elements = []
        for page in self.pages:
            elements.extend(page.elements)
        return elements


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
                elements = self._build_elements(page, i + 1, images)

                page_content = PageContent(
                    page_number=i + 1,
                    text=text,
                    lines=lines,
                    images=images,
                    elements=elements,
                )
                self._pages.append(page_content)

        return self._pages

    def _build_elements(
        self,
        page: pdfplumber.page.Page,
        page_number: int,
        images: List[ImageContent],
    ) -> List[ContentElement]:
        words = page.extract_words()
        if not words and not images:
            return []

        lines_by_y = defaultdict(list)
        for w in words:
            y_key = round(w["top"], 0)
            lines_by_y[y_key].append(w)

        text_blocks = []
        sorted_ys = sorted(lines_by_y.keys())
        for y in sorted_ys:
            line_words = sorted(lines_by_y[y], key=lambda w: w["x0"])
            line_text = " ".join([w["text"] for w in line_words])
            top = min(w["top"] for w in line_words)
            bottom = max(w["bottom"] for w in line_words)
            text_blocks.append(TextBlock(top=top, bottom=bottom, text=line_text))

        merged_blocks = self._merge_adjacent_blocks(text_blocks)

        elements = []
        for block in merged_blocks:
            elements.append(
                ContentElement(
                    element_type="text",
                    top=block.top,
                    bottom=block.bottom,
                    text=block.text,
                )
            )
        for img in images:
            elements.append(
                ContentElement(
                    element_type="image",
                    top=img.top,
                    bottom=img.bottom,
                    image=img,
                )
            )

        elements.sort(key=lambda e: (e.top, e.bottom))
        return elements

    @staticmethod
    def _merge_adjacent_blocks(blocks: List[TextBlock]) -> List[TextBlock]:
        if not blocks:
            return []
        merged = [blocks[0]]
        for block in blocks[1:]:
            prev = merged[-1]
            gap = block.top - prev.bottom
            if gap < 5:
                prev.bottom = max(prev.bottom, block.bottom)
                prev.text += " " + block.text
            else:
                merged.append(block)
        return merged

    def _extract_images(
        self, page: pdfplumber.page.Page, page_number: int
    ) -> List[ImageContent]:
        images = []
        seen_positions = set()
        try:
            for img in page.images:
                x0 = float(img.get("x0", 0))
                y0 = float(img.get("top", img.get("y0", 0)))
                x1 = float(img.get("x1", 0))
                y1 = float(img.get("bottom", img.get("y1", 0)))
                width = x1 - x0
                height = y1 - y0

                if width < 10 or height < 10:
                    continue

                pos_key = (round(x0, 0), round(y0, 0), round(x1, 0), round(y1, 0))
                if pos_key in seen_positions:
                    continue
                seen_positions.add(pos_key)

                self._image_counter += 1
                image_id = f"img_{page_number}_{self._image_counter}"

                try:
                    image_data, img_format = self._extract_image_data(
                        page, img, x0, y0, x1, y1
                    )
                    if image_data:
                        images.append(
                            ImageContent(
                                image_id=image_id,
                                page_number=page_number,
                                top=y0,
                                bottom=y1,
                                image_data=image_data,
                                format=img_format,
                            )
                        )
                except Exception as e:
                    print(
                        f"Warning: Could not extract image {image_id} on page {page_number}: {e}"
                    )
                    continue
        except Exception as e:
            print(f"Warning: Could not extract images from page {page_number}: {e}")
        return images

    def _extract_image_data(
        self,
        page: pdfplumber.page.Page,
        img: dict,
        x0: float,
        y0: float,
        x1: float,
        y1: float,
    ) -> tuple:
        if "stream" in img:
            stream = img["stream"]
            raw_data = stream.get_data()
            fmt = self._detect_image_format(raw_data)
            if fmt:
                return raw_data, fmt

        try:
            bbox = (x0, y0, x1, y1)
            page_height = page.height
            cropped = page.within_bbox(bbox)
            pil_image = cropped.to_image(resolution=150).original
            buffer = io.BytesIO()
            if pil_image.mode in ("RGBA", "LA", "P"):
                pil_image = pil_image.convert("RGB")
            pil_image.save(buffer, format="PNG", optimize=True)
            return buffer.getvalue(), "png"
        except Exception:
            pass

        try:
            padding = 2
            safe_x0 = max(0, x0 - padding)
            safe_y0 = max(0, y0 - padding)
            safe_x1 = min(page.width, x1 + padding)
            safe_y1 = min(page.height, y1 + padding)
            bbox = (safe_x0, safe_y0, safe_x1, safe_y1)
            cropped = page.within_bbox(bbox)
            pil_image = cropped.to_image(resolution=150).original
            buffer = io.BytesIO()
            if pil_image.mode in ("RGBA", "LA", "P"):
                pil_image = pil_image.convert("RGB")
            pil_image.save(buffer, format="PNG", optimize=True)
            return buffer.getvalue(), "png"
        except Exception:
            pass

        return None, None

    @staticmethod
    def _detect_image_format(data: bytes) -> Optional[str]:
        if len(data) < 4:
            return None
        if data[:8] == b"\x89PNG\r\n\x1a\n":
            return "png"
        if data[:3] == b"\xff\xd8\xff":
            return "jpeg"
        if data[:2] == b"BM":
            return "bmp"
        if data[:6] in (b"GIF87a", b"GIF89a"):
            return "gif"
        return None

    def get_page(self, page_number: int) -> PageContent:
        pages = self.extract_all_pages()
        idx = page_number - 1
        if 0 <= idx < len(pages):
            return pages[idx]
        raise IndexError(f"Page {page_number} out of range (1-{len(pages)})")

    def get_page_count(self) -> int:
        return len(self.extract_all_pages())

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

    def elements_to_html(self, elements: List[ContentElement]) -> str:
        html_parts = []
        text_buffer = []

        for elem in elements:
            if elem.element_type == "text":
                text_buffer.append(elem.text)
            elif elem.element_type == "image":
                if text_buffer:
                    combined = "\n".join(text_buffer)
                    html_parts.append(self.text_to_html_paragraphs(combined))
                    text_buffer = []

                if elem.image:
                    img_html = self._build_image_html(elem.image)
                    html_parts.append(img_html)

        if text_buffer:
            combined = "\n".join(text_buffer)
            html_parts.append(self.text_to_html_paragraphs(combined))

        return "\n".join(html_parts)

    def _build_image_html(self, img: ImageContent) -> str:
        escaped_src = self.html_escape(img.file_name)
        escaped_alt = self.html_escape(f"Image from page {img.page_number}")
        return f'<div class="image-container"><img src="{escaped_src}" alt="{escaped_alt}" class="chapter-image"/></div>'
