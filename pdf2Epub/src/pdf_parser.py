import os
import io
from typing import List, Optional, Tuple, Dict
from dataclasses import dataclass, field
import PyPDF2
import pdfplumber
from PIL import Image


@dataclass
class PdfImage:
    image_id: str
    page_idx: int
    data: bytes
    format: str
    width: int = 0
    height: int = 0


class PdfParser:
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.pdf_reader = None
        self.plumber_pdf = None
        self._text_cache: List[str] = []
        self._metadata = {}
        self._images: List[PdfImage] = []
        self._images_by_page: Dict[int, List[PdfImage]] = {}

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
        self._images = []
        self._images_by_page = {}

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

    def extract_all_images(self) -> List[PdfImage]:
        if self._images:
            return self._images
        
        self._images = []
        self._images_by_page = {}
        
        total_pages = self.get_total_pages()
        image_counter = 0
        
        for page_idx in range(total_pages):
            page_images = self._extract_page_images(page_idx, image_counter)
            if page_images:
                self._images.extend(page_images)
                self._images_by_page[page_idx] = page_images
                image_counter += len(page_images)
        
        return self._images

    def _extract_page_images(self, page_idx: int, start_image_id: int) -> List[PdfImage]:
        images = []
        
        try:
            if self.plumber_pdf:
                page = self.plumber_pdf.pages[page_idx]
                page_imgs = page.images
                
                for i, img in enumerate(page_imgs):
                    try:
                        image_data = img['stream'].get_data()
                        img_format = img.get('type', 'jpeg').lower()
                        if img_format == 'dct':
                            img_format = 'jpeg'
                        elif img_format == 'jp2':
                            img_format = 'jpeg2000'
                        
                        width = img.get('width', 0)
                        height = img.get('height', 0)
                        
                        if width == 0 or height == 0:
                            try:
                                with Image.open(io.BytesIO(image_data)) as pil_img:
                                    width, height = pil_img.size
                            except Exception:
                                pass
                        
                        pdf_image = PdfImage(
                            image_id=f'image_{page_idx + 1}_{start_image_id + i + 1}',
                            page_idx=page_idx,
                            data=image_data,
                            format=img_format,
                            width=width,
                            height=height
                        )
                        images.append(pdf_image)
                    except Exception as e:
                        print(f"  提取第 {page_idx + 1} 页图片时出错: {e}")
                        continue
        except Exception as e:
            print(f"  处理第 {page_idx + 1} 页图片时出错: {e}")
        
        if not images and self.pdf_reader:
            try:
                page = self.pdf_reader.pages[page_idx]
                if '/XObject' in page['/Resources']:
                    xObject = page['/Resources']['/XObject'].get_object()
                    for obj_key in xObject:
                        obj = xObject[obj_key].get_object()
                        if obj.get('/Subtype') == '/Image':
                            try:
                                image_data = obj.get_data()
                                img_format = 'jpeg'
                                if obj.get('/Filter') == '/FlateDecode':
                                    img_format = 'png'
                                elif obj.get('/Filter') == '/DCTDecode':
                                    img_format = 'jpeg'
                                elif obj.get('/Filter') == '/JPXDecode':
                                    img_format = 'jpeg2000'
                                
                                width = obj.get('/Width', 0)
                                height = obj.get('/Height', 0)
                                
                                pdf_image = PdfImage(
                                    image_id=f'image_{page_idx + 1}_{start_image_id + len(images) + 1}',
                                    page_idx=page_idx,
                                    data=image_data,
                                    format=img_format,
                                    width=width,
                                    height=height
                                )
                                images.append(pdf_image)
                            except Exception as e:
                                print(f"  提取第 {page_idx + 1} 页图片 (备用方法) 时出错: {e}")
                                continue
            except Exception as e:
                print(f"  备用方法提取第 {page_idx + 1} 页图片时出错: {e}")
        
        return images

    def get_images_by_page(self, page_idx: int) -> List[PdfImage]:
        if not self._images:
            self.extract_all_images()
        return self._images_by_page.get(page_idx, [])

    def get_images_by_page_range(self, start_page: int, end_page: int) -> List[PdfImage]:
        if not self._images:
            self.extract_all_images()
        
        result = []
        for page_idx in range(start_page, min(end_page + 1, self.get_total_pages())):
            result.extend(self._images_by_page.get(page_idx, []))
        return result

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
