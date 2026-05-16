import os
import io
from typing import List, Optional, Tuple, Dict, Any
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
    x0: float = 0.0
    y0: float = 0.0
    x1: float = 0.0
    y1: float = 0.0
    page_height: float = 0.0


@dataclass
class TextBlock:
    text: str
    page_idx: int
    x0: float
    y0: float
    x1: float
    y1: float
    font_size: float = 0.0
    is_heading: bool = False


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
        
        try:
            fitz_images = self._extract_images_with_fitz()
            if fitz_images:
                for img in fitz_images:
                    page_idx = img.page_idx
                    if page_idx not in self._images_by_page:
                        self._images_by_page[page_idx] = []
                    self._images_by_page[page_idx].append(img)
                    self._images.append(img)
                print(f"  使用 PyMuPDF 提取了 {len(self._images)} 张图片")
                return self._images
        except Exception as e:
            print(f"  PyMuPDF 提取图片失败，使用备用方法: {e}")
        
        for page_idx in range(total_pages):
            page_images = self._extract_page_images(page_idx, image_counter)
            if page_images:
                self._images.extend(page_images)
                self._images_by_page[page_idx] = page_images
                image_counter += len(page_images)
        
        return self._images

    def _extract_images_with_fitz(self) -> List[PdfImage]:
        import fitz
        
        fitz_doc = fitz.open(self.pdf_path)
        images = []
        
        for page_idx in range(len(fitz_doc)):
            page = fitz_doc[page_idx]
            page_height = page.rect.height
            
            image_list = page.get_images(full=True)
            
            for i, img in enumerate(image_list):
                try:
                    xref = img[0]
                    base_image = fitz_doc.extract_image(xref)
                    image_data = base_image["image"]
                    img_format = base_image["ext"]
                    
                    pil_img = Image.open(io.BytesIO(image_data))
                    pil_img.load()
                    width, height = pil_img.size
                    
                    if pil_img.mode not in ('RGB', 'L'):
                        if pil_img.mode in ('RGBA', 'LA', 'P'):
                            background = Image.new('RGB', pil_img.size, (255, 255, 255))
                            if pil_img.mode == 'P':
                                pil_img = pil_img.convert('RGBA')
                            if pil_img.mode in ('RGBA', 'LA'):
                                mask = pil_img.split()[-1]
                                background.paste(pil_img, mask=mask)
                            else:
                                background.paste(pil_img)
                            pil_img = background
                        else:
                            pil_img = pil_img.convert('RGB')
                    
                    output = io.BytesIO()
                    pil_img.save(output, format='JPEG', quality=95)
                    image_data = output.getvalue()
                    img_format = 'jpeg'
                    
                    rect = page.get_image_rects(xref)
                    x0, y0, x1, y1 = 0, 0, 0, 0
                    if rect and len(rect) > 0:
                        r = rect[0]
                        x0, y0, x1, y1 = r.x0, r.y0, r.x1, r.y1
                    
                    pdf_image = PdfImage(
                        image_id=f'image_{page_idx + 1}_{len(images) + 1}',
                        page_idx=page_idx,
                        data=image_data,
                        format=img_format,
                        width=width,
                        height=height,
                        x0=x0,
                        y0=y0,
                        x1=x1,
                        y1=y1,
                        page_height=page_height
                    )
                    images.append(pdf_image)
                except Exception as e:
                    print(f"  Fitz 提取第 {page_idx + 1} 页第 {i + 1} 张图片失败: {e}")
                    continue
        
        fitz_doc.close()
        return images

    def _extract_page_images(self, page_idx: int, start_image_id: int) -> List[PdfImage]:
        images = []
        page_height = 0.0
        
        try:
            if self.plumber_pdf:
                page = self.plumber_pdf.pages[page_idx]
                page_height = float(page.height) if page.height else 0.0
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
                        
                        x0 = float(img.get('x0', 0))
                        y0 = float(img.get('y0', 0))
                        x1 = float(img.get('x1', 0))
                        y1 = float(img.get('y1', 0))
                        
                        valid_data, valid_format = self._validate_and_convert_image(image_data, img_format, page_idx, i)
                        if valid_data is None or len(valid_data) == 0:
                            continue
                        
                        if width == 0 or height == 0:
                            try:
                                with Image.open(io.BytesIO(valid_data)) as pil_img:
                                    width, height = pil_img.size
                            except Exception:
                                pass
                        
                        pdf_image = PdfImage(
                            image_id=f'image_{page_idx + 1}_{start_image_id + i + 1}',
                            page_idx=page_idx,
                            data=valid_data,
                            format=valid_format,
                            width=width,
                            height=height,
                            x0=x0,
                            y0=y0,
                            x1=x1,
                            y1=y1,
                            page_height=page_height
                        )
                        images.append(pdf_image)
                    except Exception as e:
                        continue
        except Exception as e:
            pass
        
        if self.pdf_reader:
            try:
                page = self.pdf_reader.pages[page_idx]
                if '/XObject' in page['/Resources']:
                    xObject = page['/Resources']['/XObject'].get_object()
                    for obj_key in xObject:
                        obj = xObject[obj_key].get_object()
                        if obj.get('/Subtype') == '/Image':
                            try:
                                image_data = self._extract_image_data_with_fallback(obj, page_idx, len(images))
                                if image_data is None:
                                    continue
                                
                                valid_data, valid_format = self._validate_and_convert_image(image_data, 'jpeg', page_idx, len(images))
                                if valid_data is None or len(valid_data) == 0:
                                    continue
                                
                                width = obj.get('/Width', 0)
                                height = obj.get('/Height', 0)
                                if width == 0 or height == 0:
                                    try:
                                        with Image.open(io.BytesIO(valid_data)) as pil_img:
                                            width, height = pil_img.size
                                    except Exception:
                                        pass
                                
                                data_hash = hash(valid_data[:1000]) if len(valid_data) > 1000 else hash(valid_data)
                                exists = False
                                for existing_img in images:
                                    existing_hash = hash(existing_img.data[:1000]) if len(existing_img.data) > 1000 else hash(existing_img.data)
                                    if existing_hash == data_hash:
                                        exists = True
                                        break
                                
                                if not exists:
                                    pdf_image = PdfImage(
                                        image_id=f'image_{page_idx + 1}_{start_image_id + len(images) + 1}',
                                        page_idx=page_idx,
                                        data=valid_data,
                                        format=valid_format,
                                        width=width,
                                        height=height,
                                        x0=0,
                                        y0=0,
                                        x1=0,
                                        y1=0,
                                        page_height=page_height
                                    )
                                    images.append(pdf_image)
                            except Exception as e:
                                continue
            except Exception as e:
                pass
        
        return images

    def _extract_image_data_with_fallback(self, obj, page_idx: int, img_idx: int) -> Optional[bytes]:
        try:
            raw_data = obj.get_data()
            
            filter_type = obj.get('/Filter')
            if isinstance(filter_type, list):
                try:
                    return self._handle_multi_filter(obj, page_idx, img_idx, raw_data)
                except:
                    pass
            
            if filter_type == '/FlateDecode':
                try:
                    width = obj.get('/Width', 0)
                    height = obj.get('/Height', 0)
                    bits_per_component = obj.get('/BitsPerComponent', 8)
                    color_space = obj.get('/ColorSpace')
                    
                    if width > 0 and height > 0:
                        mode = 'RGB'
                        if color_space == '/DeviceGray':
                            mode = 'L'
                        elif color_space == '/DeviceRGB':
                            mode = 'RGB'
                        elif color_space == '/DeviceCMYK':
                            mode = 'CMYK'
                        elif isinstance(color_space, list):
                            if color_space[0] == '/ICCBased':
                                mode = 'RGB'
                            elif color_space[0] == '/DeviceN':
                                mode = 'RGB'
                        
                        stride = 0
                        if mode == 'L':
                            stride = width
                        elif mode == 'RGB':
                            stride = width * 3
                        elif mode == 'CMYK':
                            stride = width * 4
                        
                        img = Image.frombytes(mode, (width, height), raw_data, 'raw', mode, stride)
                        if mode == 'CMYK':
                            img = img.convert('RGB')
                        output = io.BytesIO()
                        img.save(output, format='JPEG', quality=95)
                        return output.getvalue()
                except Exception as e:
                    pass
            
            if filter_type == '/CCITTFaxDecode':
                try:
                    width = obj.get('/Width', 0)
                    height = obj.get('/Height', 0)
                    if width > 0 and height > 0:
                        img = Image.frombytes('1', (width, height), raw_data, 'raw', '1;I')
                        img = img.convert('RGB')
                        output = io.BytesIO()
                        img.save(output, format='JPEG', quality=95)
                        return output.getvalue()
                except Exception as e:
                    pass
            
            if filter_type == '/DCTDecode':
                try:
                    img = Image.open(io.BytesIO(raw_data))
                    img.load()
                    output = io.BytesIO()
                    if img.mode not in ('RGB', 'L'):
                        img = img.convert('RGB')
                    img.save(output, format='JPEG', quality=95)
                    return output.getvalue()
                except:
                    pass
            
            return raw_data
            
        except Exception as e:
            print(f"  [图片提取失败] 第 {page_idx + 1} 页第 {img_idx + 1} 张图片: {str(e)}")
            return None

    def _handle_multi_filter(self, obj, page_idx: int, img_idx: int, raw_data: bytes) -> Optional[bytes]:
        import zlib
        
        width = obj.get('/Width', 0)
        height = obj.get('/Height', 0)
        
        if width == 0 or height == 0:
            return None
        
        try:
            decompressed = zlib.decompress(raw_data)
            img = Image.frombytes('RGB', (width, height), decompressed)
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=95)
            return output.getvalue()
        except:
            return None

    def _validate_and_convert_image(self, image_data: bytes, original_format: str, page_idx: int, img_idx: int) -> Tuple[Optional[bytes], str]:
        if not image_data or len(image_data) < 10:
            print(f"  [图片异常] 第 {page_idx + 1} 页第 {img_idx + 1} 张图片: 数据为空或过小 ({len(image_data)} bytes)")
            return self._create_placeholder_image(f"第{page_idx + 1}页_图{img_idx + 1}"), 'jpeg'
        
        img_info = f"第 {page_idx + 1} 页第 {img_idx + 1} 张图片 (原始格式: {original_format}, 大小: {len(image_data)} bytes)"
        
        fixed_data = self._try_fix_image_data(image_data, original_format)
        if fixed_data is not None:
            if self._validate_image_data(fixed_data, 'jpeg'):
                return fixed_data, 'jpeg'
        
        try:
            img = Image.open(io.BytesIO(image_data))
            img.load()
            
            img_size = img.size
            img_mode = img.mode
            img_format = img.format
            
            if img_format and img_format.lower() in ['jpeg', 'png', 'gif'] and img_mode in ('RGB', 'L'):
                if self._validate_image_data(image_data, img_format.lower()):
                    return image_data, img_format.lower()
            
            output = io.BytesIO()
            img = Image.open(io.BytesIO(image_data))
            
            if img.mode in ('RGBA', 'LA', 'P', 'PA'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode in ('P', 'PA'):
                    img = img.convert('RGBA')
                if img.mode in ('RGBA', 'LA'):
                    mask = img.split()[-1]
                    background.paste(img, mask=mask)
                else:
                    background.paste(img)
                img = background
            elif img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            
            img.save(output, format='JPEG', quality=95, optimize=True)
            converted_data = output.getvalue()
            
            if self._validate_image_data(converted_data, 'jpeg'):
                return converted_data, 'jpeg'
            else:
                print(f"  [图片转换失败] {img_info}: 转换后验证不通过，使用占位图")
                return self._create_placeholder_image(f"第{page_idx + 1}页_图{img_idx + 1}"), 'jpeg'
                
        except Exception as e:
            print(f"  [图片异常] {img_info}: {str(e)}，使用占位图")
            return self._create_placeholder_image(f"第{page_idx + 1}页_图{img_idx + 1}"), 'jpeg'

    def _try_fix_image_data(self, image_data: bytes, original_format: str) -> Optional[bytes]:
        try:
            if len(image_data) > 100:
                header = image_data[:10]
                
                if original_format == 'jpeg' or original_format == 'dct':
                    if not (header.startswith(b'\xff\xd8') and header.endswith(b'\xff\xd9')):
                        pass
                
                if original_format == 'png':
                    if header.startswith(b'\x89PNG'):
                        try:
                            img = Image.open(io.BytesIO(image_data))
                            img.load()
                            output = io.BytesIO()
                            if img.mode not in ('RGB', 'L'):
                                if img.mode in ('RGBA', 'LA', 'P'):
                                    background = Image.new('RGB', img.size, (255, 255, 255))
                                    if img.mode == 'P':
                                        img = img.convert('RGBA')
                                    if img.mode in ('RGBA', 'LA'):
                                        mask = img.split()[-1]
                                        background.paste(img, mask=mask)
                                    else:
                                        background.paste(img)
                                    img = background
                                else:
                                    img = img.convert('RGB')
                            img.save(output, format='JPEG', quality=95)
                            return output.getvalue()
                        except:
                            pass
            
            if original_format in ['jpeg', 'jpg', 'dct', 'jpeg2000', 'jp2']:
                if image_data.startswith(b'\xff\xd8\xff'):
                    try:
                        img = Image.open(io.BytesIO(image_data))
                        img.load()
                        output = io.BytesIO()
                        if img.mode not in ('RGB', 'L'):
                            img = img.convert('RGB')
                        img.save(output, format='JPEG', quality=95)
                        return output.getvalue()
                    except:
                        pass
            
            return None
        except:
            return None

    def _validate_image_data(self, image_data: bytes, img_format: str) -> bool:
        try:
            img = Image.open(io.BytesIO(image_data))
            img.load()
            
            if img_format == 'jpeg' and img.format not in ('JPEG', 'JPG'):
                return False
            if img_format == 'png' and img.format != 'PNG':
                return False
            if img_format == 'gif' and img.format != 'GIF':
                return False
            
            if img.size[0] <= 0 or img.size[1] <= 0:
                return False
            
            if len(image_data) < 100:
                return False
            
            return True
        except Exception:
            return False

    def _create_placeholder_image(self, label: str = 'Image') -> bytes:
        try:
            output = io.BytesIO()
            img = Image.new('RGB', (400, 300), color='#f5f5f5')
            from PIL import ImageDraw, ImageFont
            draw = ImageDraw.Draw(img)
            
            draw.rectangle([10, 10, 390, 290], outline='#cccccc', width=2)
            draw.rectangle([20, 20, 380, 280], outline='#dddddd', width=1)
            
            icon_size = 80
            icon_x = (400 - icon_size) // 2
            icon_y = 80
            draw.rectangle([icon_x, icon_y, icon_x + icon_size, icon_y + icon_size], outline='#999999', width=2)
            draw.line([icon_x + 10, icon_y + icon_size - 10, icon_x + 30, icon_y + icon_size - 30], fill='#999999', width=2)
            draw.line([icon_x + 30, icon_y + icon_size - 30, icon_x + 50, icon_y + icon_size - 50], fill='#999999', width=2)
            draw.line([icon_x + 50, icon_y + icon_size - 50, icon_x + 70, icon_y + icon_size - 20], fill='#999999', width=2)
            draw.ellipse([icon_x + 50, icon_y + 20, icon_x + 70, icon_y + 40], outline='#999999', width=2)
            
            try:
                font = ImageFont.truetype('/Library/Fonts/Arial.ttf', 18)
                small_font = ImageFont.truetype('/Library/Fonts/Arial.ttf', 12)
            except:
                font = ImageFont.load_default()
                small_font = ImageFont.load_default()
            
            text = '图片加载失败'
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            draw.text(((400 - text_width) / 2, 180), text, fill='#666666', font=font)
            
            label_bbox = draw.textbbox((0, 0), label, font=small_font)
            label_width = label_bbox[2] - label_bbox[0]
            draw.text(((400 - label_width) / 2, 220), label, fill='#999999', font=small_font)
            
            img.save(output, format='JPEG', quality=85, optimize=True)
            return output.getvalue()
        except Exception as e:
            print(f"  [占位图生成失败]: {str(e)}")
            return b''

    def extract_text_blocks(self, start_page: int = 0, end_page: Optional[int] = None) -> List[TextBlock]:
        if end_page is None:
            end_page = self.get_total_pages() - 1
        
        text_blocks = []
        
        try:
            for page_idx in range(start_page, min(end_page + 1, self.get_total_pages())):
                if self.plumber_pdf:
                    page = self.plumber_pdf.pages[page_idx]
                    
                    words = page.extract_words(keep_blank_chars=False, use_text_flow=True)
                    
                    current_line = []
                    current_line_y = None
                    current_line_x = None
                    current_line_x1 = None
                    
                    for word in words:
                        word_text = word.get('text', '')
                        if not word_text.strip():
                            continue
                        
                        word_y0 = float(word.get('top', 0))
                        word_x0 = float(word.get('x0', 0))
                        word_y1 = float(word.get('bottom', 0))
                        word_x1 = float(word.get('x1', 0))
                        
                        if current_line_y is None or abs(word_y0 - current_line_y) > 5:
                            if current_line:
                                line_text = ' '.join(current_line)
                                block = TextBlock(
                                    text=line_text,
                                    page_idx=page_idx,
                                    x0=current_line_x,
                                    y0=current_line_y,
                                    x1=current_line_x1,
                                    y1=current_line_y + 12
                                )
                                text_blocks.append(block)
                            current_line = [word_text]
                            current_line_y = word_y0
                            current_line_x = word_x0
                            current_line_x1 = word_x1
                        else:
                            current_line.append(word_text)
                            current_line_x1 = max(current_line_x1 or 0, word_x1)
                    
                    if current_line:
                        line_text = ' '.join(current_line)
                        block = TextBlock(
                            text=line_text,
                            page_idx=page_idx,
                            x0=current_line_x or 0,
                            y0=current_line_y or 0,
                            x1=current_line_x1 or 0,
                            y1=(current_line_y or 0) + 12
                        )
                        text_blocks.append(block)
        except Exception as e:
            print(f"提取文本块时出错: {e}")
        
        return text_blocks

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
