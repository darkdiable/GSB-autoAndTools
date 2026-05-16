import re
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class Chapter:
    title: str
    page: int
    level: int = 1
    children: List['Chapter'] = field(default_factory=list)
    content_start_page: Optional[int] = None
    content_end_page: Optional[int] = None


class TocExtractor:
    def __init__(self):
        self.chapters: List[Chapter] = []
        self.chapter_patterns = [
            re.compile(r'^\s*(Chapter\s*\d+[\.\:：]?\s*.*)$', re.IGNORECASE),
            re.compile(r'^\s*(第\s*\d+\s*[章节篇讲]\s*.*)$'),
            re.compile(r'^\s*(\d+[\.\:：]\s*[A-Z][^a-z].*)$'),
            re.compile(r'^\s*(\d+\.\d+\s+.*)$'),
            re.compile(r'^\s*(Appendix\s*[A-Z][\.\:：]?\s*.*)$', re.IGNORECASE),
            re.compile(r'^\s*(附录\s*[A-Z0-9][\.\:：]?\s*.*)$'),
            re.compile(r'^\s*(Preface|Foreword|Introduction|Abstract|摘要|前言|目录|参考文献|Index)$', re.IGNORECASE),
        ]

    def extract_from_pdf(self, pdf_reader, pdf_texts: List[str]) -> List[Chapter]:
        self.chapters = []
        
        outline = self._try_extract_outline(pdf_reader)
        if outline:
            self.chapters = self._parse_outline(outline, pdf_texts)
            if self.chapters:
                return self.chapters
        
        self.chapters = self._extract_from_text(pdf_texts)
        return self.chapters

    def _try_extract_outline(self, pdf_reader) -> Optional[List]:
        try:
            if hasattr(pdf_reader, 'outline'):
                return pdf_reader.outline
            if hasattr(pdf_reader, 'getOutlines'):
                return pdf_reader.getOutlines()
        except Exception:
            pass
        return None

    def _parse_outline(self, outline: List, pdf_texts: List[str], level: int = 1) -> List[Chapter]:
        chapters = []
        for item in outline:
            if isinstance(item, list):
                child_chapters = self._parse_outline(item, pdf_texts, level + 1)
                if chapters:
                    chapters[-1].children.extend(child_chapters)
            else:
                try:
                    title = item.title if hasattr(item, 'title') else str(item)
                    page = pdf_reader.get_destination_page_number(item) if hasattr(pdf_reader, 'get_destination_page_number') else 0
                    chapter = Chapter(title=title.strip(), page=page, level=level)
                    chapters.append(chapter)
                except Exception:
                    continue
        
        self._fill_content_pages(chapters, len(pdf_texts))
        return chapters

    def _extract_from_text(self, pdf_texts: List[str]) -> List[Chapter]:
        chapters = []
        potential_chapters = []
        
        for page_idx, text in enumerate(pdf_texts):
            lines = text.split('\n')
            for line in lines:
                line = line.strip()
                if not line or len(line) > 100:
                    continue
                
                for pattern in self.chapter_patterns:
                    match = pattern.match(line)
                    if match:
                        title = match.group(1).strip()
                        if len(title) < 5 or len(title) > 100:
                            continue
                        potential_chapters.append(Chapter(title=title, page=page_idx))
                        break
        
        chapters = self._filter_chapters(potential_chapters)
        self._fill_content_pages(chapters, len(pdf_texts))
        return chapters

    def _filter_chapters(self, potential_chapters: List[Chapter]) -> List[Chapter]:
        if not potential_chapters:
            return []
        
        seen_titles = set()
        filtered = []
        
        for chapter in potential_chapters:
            title_key = chapter.title.lower()
            if title_key in seen_titles:
                continue
            seen_titles.add(title_key)
            
            level = self._determine_level(chapter.title)
            chapter.level = level
            filtered.append(chapter)
        
        return self._build_hierarchy(filtered)

    def _determine_level(self, title: str) -> int:
        if re.match(r'^\d+\.\d+\.\d+', title):
            return 3
        if re.match(r'^\d+\.\d+', title):
            return 2
        if re.match(r'^(Chapter|第|附录|Appendix)', title, re.IGNORECASE):
            return 1
        if re.match(r'^\d+[\.\:]', title):
            return 1
        return 1

    def _build_hierarchy(self, chapters: List[Chapter]) -> List[Chapter]:
        if not chapters:
            return []
        
        root = []
        stack = []
        
        for chapter in chapters:
            while stack and stack[-1].level >= chapter.level:
                stack.pop()
            
            if stack:
                stack[-1].children.append(chapter)
            else:
                root.append(chapter)
            
            stack.append(chapter)
        
        return root

    def _fill_content_pages(self, chapters: List[Chapter], total_pages: int):
        all_chapters = self._flatten_chapters(chapters)
        
        for i, chapter in enumerate(all_chapters):
            chapter.content_start_page = chapter.page
            if i < len(all_chapters) - 1:
                chapter.content_end_page = all_chapters[i + 1].page - 1
            else:
                chapter.content_end_page = total_pages - 1
            
            if chapter.children:
                self._fill_content_pages(chapter.children, total_pages)

    def _flatten_chapters(self, chapters: List[Chapter]) -> List[Chapter]:
        flattened = []
        for chapter in chapters:
            flattened.append(chapter)
            if chapter.children:
                flattened.extend(self._flatten_chapters(chapter.children))
        return flattened

    def get_toc_for_epub(self) -> List[Tuple[str, str]]:
        toc_items = []
        self._collect_toc_items(self.chapters, toc_items)
        return toc_items

    def _collect_toc_items(self, chapters: List[Chapter], toc_items: List[Tuple[str, str]], prefix: str = ''):
        for i, chapter in enumerate(chapters):
            chapter_id = f'chapter_{prefix}{i + 1}'
            toc_items.append((chapter.title, chapter_id))
            if chapter.children:
                self._collect_toc_items(chapter.children, toc_items, f'{prefix}{i + 1}_')
