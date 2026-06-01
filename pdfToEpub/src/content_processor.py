import re
from dataclasses import dataclass, field
from typing import List

import pdfplumber


@dataclass
class PageContent:
    page_number: int
    text: str
    lines: List[str] = field(default_factory=list)


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


class ContentProcessor:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self._pages: List[PageContent] = []

    def extract_all_pages(self) -> List[PageContent]:
        if self._pages:
            return self._pages

        with pdfplumber.open(self.pdf_path) as pdf:
            for i, page in enumerate(pdf.pages):
                text = page.extract_text() or ""
                lines = text.split("\n") if text else []
                page_content = PageContent(
                    page_number=i + 1,
                    text=text,
                    lines=lines,
                )
                self._pages.append(page_content)

        return self._pages

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
