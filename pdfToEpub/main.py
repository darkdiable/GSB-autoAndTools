import argparse
import os
import sys

from src.epub_builder import convert_pdf_to_epub


def find_pdf_files(pdf_dir: str) -> list:
    pdf_files = []
    if not os.path.isdir(pdf_dir):
        return pdf_files
    for filename in sorted(os.listdir(pdf_dir)):
        if filename.lower().endswith(".pdf"):
            pdf_files.append(os.path.join(pdf_dir, filename))
    return pdf_files


def main():
    parser = argparse.ArgumentParser(
        description="Convert PDF files to EPUB format with chapter navigation"
    )
    parser.add_argument(
        "--pdf-dir",
        default=os.path.join(os.path.dirname(__file__), "pdf"),
        help="Directory containing PDF files (default: ./pdf)",
    )
    parser.add_argument(
        "--epub-dir",
        default=os.path.join(os.path.dirname(__file__), "epub"),
        help="Directory for output EPUB files (default: ./epub)",
    )
    parser.add_argument(
        "--author",
        default="Unknown",
        help="Author name for the EPUB metadata",
    )
    parser.add_argument(
        "--language",
        default="zh",
        help="Language code for the EPUB (default: zh)",
    )
    parser.add_argument(
        "--file",
        default=None,
        help="Convert a single PDF file instead of the whole directory",
    )

    args = parser.parse_args()

    if args.file:
        if not os.path.isfile(args.file):
            print(f"Error: File not found: {args.file}")
            sys.exit(1)
        pdf_files = [args.file]
    else:
        pdf_files = find_pdf_files(args.pdf_dir)
        if not pdf_files:
            print(f"No PDF files found in: {args.pdf_dir}")
            sys.exit(1)

    os.makedirs(args.epub_dir, exist_ok=True)

    success_count = 0
    for pdf_path in pdf_files:
        filename = os.path.basename(pdf_path)
        book_title = os.path.splitext(filename)[0]
        print(f"Converting: {filename}")

        try:
            output_path = convert_pdf_to_epub(
                pdf_path=pdf_path,
                output_dir=args.epub_dir,
                book_title=book_title,
                book_author=args.author,
                language=args.language,
            )
            print(f"  -> Created: {output_path}")
            success_count += 1
        except Exception as e:
            print(f"  -> Error: {e}")

    print(f"\nDone: {success_count}/{len(pdf_files)} file(s) converted.")


if __name__ == "__main__":
    main()
