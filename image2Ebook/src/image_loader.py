import os
import re
from pathlib import Path
from typing import List, Optional, Tuple


class ImageLoader:
    SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp'}

    def __init__(self, img_dir: str):
        self.img_dir = Path(img_dir)
        if not self.img_dir.exists():
            raise FileNotFoundError(f"Image directory not found: {img_dir}")

    @staticmethod
    def _extract_number(filename: str) -> Tuple[int, str]:
        name_without_ext = os.path.splitext(filename)[0]
        if name_without_ext.lower() == 'cover':
            return (-1, name_without_ext)
        match = re.search(r'(\d+)', name_without_ext)
        if match:
            return (int(match.group(1)), name_without_ext)
        return (float('inf'), name_without_ext)

    def _is_supported_image(self, filename: str) -> bool:
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.SUPPORTED_EXTENSIONS

    def load_images(self) -> Tuple[Optional[str], List[str]]:
        all_files = os.listdir(self.img_dir)
        image_files = [f for f in all_files if self._is_supported_image(f)]
        
        if not image_files:
            raise ValueError(f"No supported images found in {self.img_dir}")

        sorted_images = sorted(image_files, key=self._extract_number)

        cover_image = None
        content_images = []

        for img in sorted_images:
            name_without_ext = os.path.splitext(img)[0].lower()
            if name_without_ext == 'cover' and cover_image is None:
                cover_image = img
            else:
                content_images.append(img)

        return cover_image, content_images

    def get_image_path(self, filename: str) -> Path:
        return self.img_dir / filename

    def get_image_info(self, filename: str) -> dict:
        filepath = self.get_image_path(filename)
        return {
            'filename': filename,
            'path': str(filepath),
            'size': os.path.getsize(filepath),
            'extension': os.path.splitext(filename)[1].lower()
        }
