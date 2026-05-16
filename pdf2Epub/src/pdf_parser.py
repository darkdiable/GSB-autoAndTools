import os
from typing import List, Optional, Tuple
import PyPDF2
import pdfplumber


class PdfParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_reader = None
        self.plumber_pdf = None
        self._text_cache: List[str] = []
        self._metadata = {}

    def open(self):
        if not os.path.exists(self.pdf_path):
            raise FileNotFoundError(f"PDF文件不存在: {self.pdf_path}")
        
        self.pdf_reader = PyPDF2.PdfReader(self.pdf_path)
        self.plumber_pdf = pdfplumber.open(self.pdf_path)
        
        try:
            if self.pdf_reader.metadata:
                self._metadata = {
                    'title': self.pdf_reader.metadata.title or os.path.splitext(os.path.basename(self.pdf_path))[0],
                    'author': self.pdf_reader.metadata.author or 'Unknown',
                    'subject': self.pdf_reader.metadata.subject or '',
                    'creator': self.pdf_reader.metadata.creator or '',
                    'producer': self.pdf_reader.metadata.producer or '',
                }
        except Exception:
            self._metadata = {
                'title': os.path.splitext(os.path.basename(self.pdf_path))[0],
                'author': 'Unknown',
                'subject': '',
                'creator': '',
                'producer': '',
            }

    def close(self):
        if self.plumber_pdf:
            self.plumber_pdf.close()
        self.pdf_reader = None
        self.plumber_pdf = None
        self._text_cache = []

    def get_total_pages(self) -> int:
        if self.pdf_reader:
            return len(self.pdf_reader.pages)
        return 0

    def extract_all_text(self, use_pdfplumber: bool = True) -> List[str]:
        if self._text_cache:
            return self._text_cache
        
        texts = []
        total_pages = self.get_total_pages()
        
        for page_idx in range(total_pages):
            text = self.extract_page_text(page_idx, use_pdfplumber)
            texts.append(text)
        
        self._text_cache = texts
        return texts

    def extract_page_text(self, page_idx: int, use_pdfplumber: bool = True) -> str:
        if page_idx < 0 or page_idx >= self.get_total_pages():
            return ''
        
        try:
            if use_pdfplumber and self.plumber_pdf:
                page = self.plumber_pdf.pages[page_idx]
                text = page.extract_text() or ''
                return self._clean_text(text)
            
            if self.pdf_reader:
                page = self.pdf_reader.pages[page_idx]
                text = page.extract_text() or ''
                return self._clean_text(text)
        except Exception as e:
            print(f"提取第 {page_idx + 1} 页文本时出错: {e}")
        
        return ''

    def extract_page_range_text(self, start_page: int, end_page: int, use_pdfplumber: bool = True) -> str:
        texts = []
        for page_idx in range(start_page, min(end_page + 1, self.get_total_pages())):
            text = self.extract_page_text(page_idx, use_pdfplumber)
            if text.strip():
                texts.append(text)
        return '\n\n'.join(texts)

    def get_metadata(self) -> dict:
        return self._metadata.copy()

    def get_pdf_reader(self):
        return self.pdf_reader

    def _clean_text(self, text: str) -> str:
        if not text:
            return ''
        
        lines = text.split('\n')
        cleaned_lines = []
        
        for line in lines:
            line = line.strip()
            if not line:
                if cleaned_lines and cleaned_lines[-1] != '':
                    cleaned_lines.append('')
                continue
            
            line = line.replace('\r', '')
            line = line.replace('\t', '    ')
            line = ' '.join(line.split())
            
            cleaned_lines.append(line)
        
        while cleaned_lines and cleaned_lines[0] == '':
            cleaned_lines.pop(0)
        while cleaned_lines and cleaned_lines[-1] == '':
            cleaned_lines.pop()
        
        return '\n'.join(cleaned_lines)

    def __enter__(self):
        self.open()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
