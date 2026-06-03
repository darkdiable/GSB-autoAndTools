import os
import re
from dataclasses import dataclass
from typing import Optional

from . import config


@dataclass
class ImageInfo:
    filepath: str
    filename: str
    basename: str
    extension: str
    sort_key: tuple
    is_cover: bool


def _extract_sort_key(filename: str) -> tuple:
    parts = re.findall(r'(\d+|\D+)', filename)
    key = []
    for part in parts:
        if part.isdigit():
            key.append((0, int(part), ""))
        else:
            key.append((1, 0, part.lower()))
    return tuple(key)


def scan_images(img_dir: Optional[str] = None) -> list[ImageInfo]:
    if img_dir is None:
        img_dir = config.IMG_DIR

    if not os.path.isdir(img_dir):
        raise FileNotFoundError(f"Image directory not found: {img_dir}")

    images = []
    for fname in os.listdir(img_dir):
        name, ext = os.path.splitext(fname)
        if ext.lower() not in config.IMAGE_EXTENSIONS:
            continue

        filepath = os.path.join(img_dir, fname)
        if not os.path.isfile(filepath):
            continue

        is_cover = name.lower() == config.COVER_FILENAME
        sort_key = _extract_sort_key(name)

        images.append(ImageInfo(
            filepath=filepath,
            filename=fname,
            basename=name,
            extension=ext.lower(),
            sort_key=sort_key,
            is_cover=is_cover,
        ))

    images.sort(key=lambda img: img.sort_key)
    return images


def get_cover_image(images: list[ImageInfo]) -> Optional[ImageInfo]:
    for img in images:
        if img.is_cover:
            return img
    return None


def get_content_images(images: list[ImageInfo]) -> list[ImageInfo]:
    return [img for img in images if not img.is_cover]


def read_image_data(img: ImageInfo) -> bytes:
    with open(img.filepath, "rb") as f:
        return f.read()


def get_image_mime_type(img: ImageInfo) -> str:
    ext = img.extension.lower()
    mime_map = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".gif": "image/gif",
        ".bmp": "image/bmp",
        ".webp": "image/webp",
        ".tiff": "image/tiff",
        ".svg": "image/svg+xml",
    }
    return mime_map.get(ext, "image/jpeg")
