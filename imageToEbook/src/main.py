import argparse
import sys

from .image_handler import scan_images, get_cover_image, get_content_images
from .epub_builder import build_epub


def main():
    parser = argparse.ArgumentParser(
        description="Convert images to EPUB ebook"
    )
    parser.add_argument(
        "--title", "-t",
        default=None,
        help="Book title (default: 'Image Ebook')",
    )
    parser.add_argument(
        "--author", "-a",
        default=None,
        help="Book author (default: 'Unknown')",
    )
    parser.add_argument(
        "--language", "-l",
        default=None,
        help="Book language code (default: 'zh')",
    )
    parser.add_argument(
        "--output", "-o",
        default=None,
        help="Output EPUB filename (default: 'output.epub')",
    )
    args = parser.parse_args()

    try:
        images = scan_images()
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    if not images:
        print("Error: No images found in the img directory.", file=sys.stderr)
        sys.exit(1)

    cover = get_cover_image(images)
    content = get_content_images(images)

    print(f"Found {len(images)} image(s):")
    if cover:
        print(f"  Cover: {cover.filename}")
    print(f"  Content pages: {len(content)}")
    for img in content:
        print(f"    - {img.filename}")

    try:
        output_path = build_epub(
            title=args.title,
            author=args.author,
            language=args.language,
            output_name=args.output,
        )
        print(f"\nEPUB generated successfully: {output_path}")
    except Exception as e:
        print(f"Error generating EPUB: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
