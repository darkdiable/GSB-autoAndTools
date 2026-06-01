import re
from dataclasses import dataclass
from typing import List, Optional, Tuple

from .content_processor import ContentProcessor, ChapterContent, PageContent


@dataclass
class ChapterInfo:
    title: str
    chapter_id: str
    page_number: int
    line_index: int = 0
    level: int = 1


class TOCProcessor:
    CHAPTER_PATTERNS = [
        re.compile(
            r"^\s*第[一二三四五六七八九十百千万零〇\d]+[章节篇部回卷]\b",
            re.UNICODE,
        ),
        re.compile(r"^\s*Chapter\s+\d+", re.IGNORECASE),
        re.compile(r"^\s*CHAPTER\s+\d+"),
        re.compile(r"^\s*Part\s+\d+", re.IGNORECASE),
        re.compile(r"^\s*PART\s+\d+"),
    ]

    def __init__(self, content_processor: ContentProcessor):
        self.content_processor = content_processor
        self._chapters: Optional[List[ChapterInfo]] = None

    def detect_chapters(self) -> List[ChapterInfo]:
        if self._chapters is not None:
            return self._chapters

        pages = self.content_processor.extract_all_pages()
        found: List[ChapterInfo] = []

        for page in pages:
            for line_idx, line in enumerate(page.lines):
                stripped = line.strip()
                if not stripped:
                    continue
                if self._is_chapter_heading(stripped):
                    level = self._detect_level(stripped)
                    chapter_id = f"chapter_{len(found) + 1}"
                    found.append(
                        ChapterInfo(
                            title=stripped,
                            chapter_id=chapter_id,
                            page_number=page.page_number,
                            line_index=line_idx,
                            level=level,
                        )
                    )
                    break

        if not found:
            found = self._split_by_pages(pages)

        self._chapters = found
        return self._chapters

    def _is_chapter_heading(self, line: str) -> bool:
        for pattern in self.CHAPTER_PATTERNS:
            if pattern.match(line):
                return True
        return False

    def _detect_level(self, title: str) -> int:
        if re.match(r"^\s*第[一二三四五六七八九十百千万零〇\d]+[篇部卷]\b", title):
            return 1
        if re.match(r"^\s*第[一二三四五六七八九十百千万零〇\d]+[章节回]\b", title):
            return 2
        if re.match(r"^\s*(Part|PART)\s+\d+", title):
            return 1
        if re.match(r"^\s*(Chapter|CHAPTER)\s+\d+", title):
            return 2
        return 2

    def _split_by_pages(self, pages: List[PageContent]) -> List[ChapterInfo]:
        chapters = []
        total = len(pages)
        step = max(1, total // 10)
        for i in range(0, total, step):
            chapter_id = f"chapter_{len(chapters) + 1}"
            end = min(i + step, total)
            title = f"Section {len(chapters) + 1} (Page {i + 1}-{end})"
            chapters.append(
                ChapterInfo(
                    title=title,
                    chapter_id=chapter_id,
                    page_number=i + 1,
                    line_index=0,
                    level=1,
                )
            )
        return chapters

    def build_chapter_contents(self) -> List[ChapterContent]:
        chapter_infos = self.detect_chapters()
        pages = self.content_processor.extract_all_pages()
        chapter_contents: List[ChapterContent] = []

        for idx, info in enumerate(chapter_infos):
            start_page_idx = info.page_number - 1
            if idx + 1 < len(chapter_infos):
                end_page_idx = chapter_infos[idx + 1].page_number - 1
            else:
                end_page_idx = len(pages)

            chapter_pages = pages[start_page_idx:end_page_idx]

            full_text_parts = []
            for pi, page in enumerate(chapter_pages):
                if page.text.strip():
                    full_text_parts.append(page.text.strip())

            chapter_content = ChapterContent(
                title=info.title,
                chapter_id=info.chapter_id,
                pages=chapter_pages,
                text="\n\n".join(full_text_parts),
            )
            chapter_contents.append(chapter_content)

        return chapter_contents

    def get_toc_items(self) -> List[Tuple[str, str, int]]:
        chapters = self.detect_chapters()
        return [(ch.title, ch.chapter_id, ch.level) for ch in chapters]
