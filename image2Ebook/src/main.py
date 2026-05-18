import argparse
import sys
import os
from pathlib import Path

from .image_loader import ImageLoader
from .epub_builder import EpubBuilder


def main():
    parser = argparse.ArgumentParser(description="Convert images to EPUB ebook")
    parser.add_argument(
        "--img-dir",
        default=None,
        help="Directory containing input images (default: ../img)"
    )
    parser.add_argument(
        "--output-dir",
        default=None,
        help="Directory for output EPUB file (default: ../epub)"
    )
    parser.add_argument(
        "--title",
        default="图片电子书",
        help="Book title (default: 图片电子书)"
    )
    parser.add_argument(
        "--author",
        default="Unknown",
        help="Book author (default: Unknown)"
    )
    parser.add_argument(
        "--output",
        default="output.epub",
        help="Output EPUB filename (default: output.epub)"
    )
    
    args = parser.parse_args()
    
    script_dir = Path(__file__).resolve().parent
    project_dir = script_dir.parent
    
    img_dir = args.img_dir or str(project_dir / "img")
    output_dir = args.output_dir or str(project_dir / "epub")
    
    print(f"Image directory: {img_dir}")
    print(f"Output directory: {output_dir}")
    print(f"Book title: {args.title}")
    print(f"Author: {args.author}")
    
    try:
        loader = ImageLoader(img_dir)
        cover_image, content_images = loader.load_images()
        
        print(f"\nFound {len(content_images)} content pages")
        if cover_image:
            print(f"Cover image: {cover_image}")
        print(f"Content images: {content_images}")
        
        builder = EpubBuilder(output_dir, book_title=args.title, author=args.author)
        epub_path = builder.build(img_dir, cover_image, content_images, args.output)
        
        print(f"\nSuccess! EPUB generated at: {epub_path}")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
