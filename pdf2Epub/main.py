#!/usr/bin/env python3
import os
import sys
import argparse
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.pdf_parser import PdfParser
from src.toc_extractor import TocExtractor, Chapter
from src.content_processor import ContentProcessor
from src.epub_generator import EpubGenerator


class PdfToEpubConverter:
    def __init__(self, pdf_dir: str, epub_dir: str):
        self.pdf_dir = pdf_dir
        self.epub_dir = epub_dir
        os.makedirs(self.pdf_dir, exist_ok=True)
        os.makedirs(self.epub_dir, exist_ok=True)

    def convert_file(self, pdf_path: str, output_filename: Optional[str] = None) -> str:
        print(f"正在处理: {os.path.basename(pdf_path)}")
        
        with PdfParser(pdf_path) as parser:
            metadata = parser.get_metadata()
            book_title = metadata.get('title', os.path.splitext(os.path.basename(pdf_path))[0])
            
            print(f"  提取PDF文本...")
            pdf_texts = parser.extract_all_text()
            total_pages = parser.get_total_pages()
            print(f"  共 {total_pages} 页")
            
            print(f"  提取图片...")
            images = parser.extract_all_images()
            print(f"  共提取 {len(images)} 张图片")
            
            print(f"  提取目录信息...")
            toc_extractor = TocExtractor()
            chapters = toc_extractor.extract_from_pdf(parser.get_pdf_reader(), pdf_texts)
            
            if not chapters:
                print(f"  警告: 未能识别到章节，将按页面自动分章")
                chapters = self._create_default_chapters(total_pages)
            
            self._print_chapter_hierarchy(chapters)
            
            print(f"  处理章节内容...")
            content_processor = ContentProcessor()
            chapter_contents = content_processor.process_chapters(chapters, parser)
            
            total_images_in_chapters = sum(len(c.images) for c in chapter_contents)
            print(f"  共处理 {len(chapter_contents)} 个章节，包含 {total_images_in_chapters} 张图片")
            
            print(f"  生成EPUB...")
            epub_generator = EpubGenerator(self.epub_dir)
            output_path = epub_generator.generate(
                book_title=book_title,
                chapters=chapters,
                chapter_contents=chapter_contents,
                metadata=metadata,
                output_filename=output_filename
            )
            
            print(f"  完成: {os.path.basename(output_path)}")
            return output_path

    def convert_all(self) -> List[str]:
        pdf_files = list(Path(self.pdf_dir).glob('*.pdf'))
        if not pdf_files:
            print(f"在 {self.pdf_dir} 中没有找到PDF文件")
            return []
        
        print(f"找到 {len(pdf_files)} 个PDF文件")
        print("=" * 50)
        
        output_files = []
        for pdf_path in pdf_files:
            try:
                output_path = self.convert_file(str(pdf_path))
                output_files.append(output_path)
            except Exception as e:
                print(f"  错误: 处理 {pdf_path.name} 时失败: {e}")
                import traceback
                traceback.print_exc()
            print("-" * 50)
        
        return output_files

    def _create_default_chapters(self, total_pages: int, pages_per_chapter: int = 20) -> List[Chapter]:
        chapters = []
        for start_page in range(0, total_pages, pages_per_chapter):
            end_page = min(start_page + pages_per_chapter - 1, total_pages - 1)
            chapter_num = len(chapters) + 1
            chapter = Chapter(
                title=f"第 {chapter_num} 部分",
                page=start_page,
                level=1,
                content_start_page=start_page,
                content_end_page=end_page
            )
            chapters.append(chapter)
        return chapters

    def _print_chapter_hierarchy(self, chapters: List[Chapter], indent: int = 0):
        for chapter in chapters:
            prefix = "  " * indent
            page_range = f" (页 {chapter.content_start_page + 1}-{chapter.content_end_page + 1})" if chapter.content_start_page is not None else ""
            print(f"  {prefix}- {chapter.title}{page_range}")
            if chapter.children:
                self._print_chapter_hierarchy(chapter.children, indent + 1)


def main():
    parser = argparse.ArgumentParser(description='PDF转EPUB工具')
    parser.add_argument(
        '--pdf-dir', 
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'pdf'),
        help='PDF文件目录 (默认: ./pdf)'
    )
    parser.add_argument(
        '--epub-dir', 
        default=os.path.join(os.path.dirname(os.path.abspath(__file__)), 'epub'),
        help='EPUB输出目录 (默认: ./epub)'
    )
    parser.add_argument(
        '--file', 
        help='指定单个PDF文件进行转换（而非转换整个目录）'
    )
    parser.add_argument(
        '--output', 
        help='输出EPUB文件名（仅在指定--file时有效）'
    )
    
    args = parser.parse_args()
    
    converter = PdfToEpubConverter(args.pdf_dir, args.epub_dir)
    
    if args.file:
        if not os.path.exists(args.file):
            print(f"错误: 文件不存在: {args.file}")
            sys.exit(1)
        converter.convert_file(args.file, args.output)
    else:
        converter.convert_all()
    
    print("处理完成!")


if __name__ == '__main__':
    main()
