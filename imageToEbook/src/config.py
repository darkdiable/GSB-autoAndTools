import os

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

IMG_DIR = os.path.join(PROJECT_ROOT, "img")

EPUB_DIR = os.path.join(PROJECT_ROOT, "epub")

BOOK_TITLE = "Image Ebook"
BOOK_AUTHOR = "Unknown"
BOOK_LANGUAGE = "zh"

COVER_FILENAME = "cover"

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", ".svg"}

EPUB_OUTPUT_NAME = "output.epub"
