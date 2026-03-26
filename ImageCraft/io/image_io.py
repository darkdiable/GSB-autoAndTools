import numpy as np
from PIL import Image
from typing import List, Tuple, Optional, Union
import os
import cv2


class ImageLoader:
    """图像加载器"""
    
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
    
    def load(self, path: str, mode: str = 'rgb') -> np.ndarray:
        """
        加载单张图像
        
        Args:
            path: 图像路径
            mode: 加载模式 ('rgb', 'grayscale', 'rgba')
        
        Returns:
            图像数组
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"图像文件不存在：{path}")
        
        ext = os.path.splitext(path)[1].lower()
        if ext not in self.supported_formats:
            raise ValueError(f"不支持的图像格式：{ext}")
        
        if mode == 'rgb':
            img = cv2.imread(path)
            if img is None:
                raise ValueError(f"无法读取图像：{path}")
            img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        elif mode == 'grayscale':
            img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
            if img is None:
                raise ValueError(f"无法读取图像：{path}")
        elif mode == 'rgba':
            img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            if img is None:
                raise ValueError(f"无法读取图像：{path}")
            if len(img.shape) == 2:
                img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGBA)
            elif img.shape[2] == 3:
                img = cv2.cvtColor(img, cv2.COLOR_RGB2RGBA)
        else:
            raise ValueError(f"未知的加载模式：{mode}")
        
        return img
    
    def load_batch(self, paths: List[str], mode: str = 'rgb') -> List[np.ndarray]:
        """
        批量加载图像
        
        Args:
            paths: 图像路径列表
            mode: 加载模式
        
        Returns:
            图像数组列表
        """
        images = []
        for path in paths:
            img = self.load(path, mode)
            images.append(img)
        
        return images
    
    def load_directory(self, directory: str, mode: str = 'rgb', 
                      recursive: bool = False) -> Tuple[List[np.ndarray], List[str]]:
        """
        加载目录中的所有图像
        
        Args:
            directory: 目录路径
            mode: 加载模式
            recursive: 是否递归加载子目录
        
        Returns:
            (图像数组列表，文件路径列表)
        """
        if not os.path.isdir(directory):
            raise NotADirectoryError(f"目录不存在：{directory}")
        
        images = []
        paths = []
        
        if recursive:
            for root, _, files in os.walk(directory):
                for file in files:
                    if self._is_image_file(file):
                        path = os.path.join(root, file)
                        img = self.load(path, mode)
                        images.append(img)
                        paths.append(path)
        else:
            for file in os.listdir(directory):
                if self._is_image_file(file):
                    path = os.path.join(directory, file)
                    img = self.load(path, mode)
                    images.append(img)
                    paths.append(path)
        
        return images, paths
    
    def _is_image_file(self, filename: str) -> bool:
        """检查是否为图像文件"""
        ext = os.path.splitext(filename)[1].lower()
        return ext in self.supported_formats


class ImageSaver:
    """图像保存器"""
    
    def __init__(self):
        self.supported_formats = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.webp']
    
    def save(self, image: np.ndarray, path: str, quality: int = 95) -> None:
        """
        保存图像
        
        Args:
            image: 图像数组
            path: 保存路径
            quality: JPEG 质量 (1-100)
        """
        ext = os.path.splitext(path)[1].lower()
        if ext not in self.supported_formats:
            raise ValueError(f"不支持的图像格式：{ext}")
        
        if len(image.shape) == 3 and image.shape[2] == 3:
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        
        if ext in ['.jpg', '.jpeg']:
            cv2.imwrite(path, image, [cv2.IMWRITE_JPEG_QUALITY, quality])
        else:
            cv2.imwrite(path, image)
    
    def save_batch(self, images: List[np.ndarray], paths: List[str], 
                  quality: int = 95) -> None:
        """
        批量保存图像
        
        Args:
            images: 图像数组列表
            paths: 保存路径列表
            quality: JPEG 质量
        """
        if len(images) != len(paths):
            raise ValueError("图像数量和路径数量不匹配")
        
        for img, path in zip(images, paths):
            self.save(img, path, quality)
    
    def save_grid(self, images: List[np.ndarray], output_path: str, 
                 rows: int, cols: int, padding: int = 2) -> None:
        """
        保存图像网格
        
        Args:
            images: 图像数组列表
            output_path: 输出路径
            rows: 行数
            cols: 列数
            padding: 图像间距
        """
        if len(images) != rows * cols:
            raise ValueError(f"需要 {rows * cols} 张图像，但提供了 {len(images)} 张")
        
        max_height = max(img.shape[0] for img in images)
        max_width = max(img.shape[1] for img in images)
        
        if len(images[0].shape) == 2:
            grid = np.ones((rows * max_height + (rows-1) * padding, 
                          cols * max_width + (cols-1) * padding), dtype=np.uint8) * 255
        else:
            channels = images[0].shape[2]
            grid = np.ones((rows * max_height + (rows-1) * padding, 
                          cols * max_width + (cols-1) * padding, channels), dtype=np.uint8) * 255
        
        for idx, img in enumerate(images):
            i = idx // cols
            j = idx % cols
            
            y_start = i * (max_height + padding)
            x_start = j * (max_width + padding)
            
            if len(img.shape) == 2:
                grid[y_start:y_start+img.shape[0], x_start:x_start+img.shape[1]] = img
            else:
                grid[y_start:y_start+img.shape[0], x_start:x_start+img.shape[1], :] = img
        
        self.save(grid, output_path)


class BatchProcessor:
    """批量处理器"""
    
    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = input_dir
        self.output_dir = output_dir
        self.loader = ImageLoader()
        self.saver = ImageSaver()
    
    def process(self, processor_func, **kwargs) -> int:
        """
        批量处理图像
        
        Args:
            processor_func: 处理函数
            **kwargs: 处理函数的参数
        
        Returns:
            处理的图像数量
        """
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        
        images, paths = self.loader.load_directory(self.input_dir)
        
        count = 0
        for img, path in zip(images, paths):
            try:
                processed = processor_func(img, **kwargs)
                
                filename = os.path.basename(path)
                output_path = os.path.join(self.output_dir, filename)
                
                self.saver.save(processed, output_path)
                count += 1
            except Exception as e:
                print(f"处理失败 {path}: {e}")
        
        return count
