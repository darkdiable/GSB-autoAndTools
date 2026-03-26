import numpy as np
from PIL import Image
from typing import Optional, Tuple, Dict, Any
import cv2


class ImageProcessor:
    """图像处理核心类"""
    
    def __init__(self):
        self.image: Optional[np.ndarray] = None
        self.original_image: Optional[np.ndarray] = None
        self.image_path: Optional[str] = None
        self.history: list = []
        self.metadata: Dict[str, Any] = {}
    
    def load_image(self, path: str) -> None:
        """加载图像"""
        try:
            img = Image.open(path)
            self.image = np.array(img)
            self.original_image = self.image.copy()
            self.image_path = path
            self.metadata = {
                'width': self.image.shape[1],
                'height': self.image.shape[0],
                'channels': self.image.shape[2] if len(self.image.shape) > 2 else 1,
                'dtype': str(self.image.dtype)
            }
            self._save_state("initial_load")
        except Exception as e:
            raise IOError(f"无法加载图像：{e}")
    
    def _save_state(self, operation: str) -> None:
        """保存当前状态到历史记录"""
        if self.image is not None:
            self.history.append({
                'operation': operation,
                'image': self.image.copy(),
                'metadata': self.metadata.copy()
            })
    
    def undo(self) -> bool:
        """撤销上一步操作"""
        if len(self.history) > 1:
            self.history.pop()
            last_state = self.history[-1]
            self.image = last_state['image'].copy()
            self.metadata = last_state['metadata'].copy()
            return True
        return False
    
    def get_image(self) -> Optional[np.ndarray]:
        """获取当前图像"""
        return self.image
    
    def save(self, path: str, quality: int = 95) -> None:
        """保存图像"""
        if self.image is None:
            raise ValueError("没有可保存的图像")
        
        img = Image.fromarray(self.image)
        img.save(path, quality=quality)
    
    def resize(self, width: int, height: int, interpolation: str = 'bilinear') -> None:
        """调整图像大小"""
        if self.image is None:
            raise ValueError("没有加载图像")
        
        interp_map = {
            'nearest': cv2.INTER_NEAREST,
            'bilinear': cv2.INTER_LINEAR,
            'bicubic': cv2.INTER_CUBIC,
            'area': cv2.INTER_AREA
        }
        
        interp_method = interp_map.get(interpolation, cv2.INTER_LINEAR)
        
        current_height, current_width = self.image.shape[:2]
        
        if width <= 0 or height <= 0:
            raise ValueError("宽度和高度必须为正数")
        
        resized = cv2.resize(self.image, (width, height), interpolation=interp_method)
        self.image = resized
        
        self.metadata['width'] = width
        self.metadata['height'] = height
        self._save_state("resize")
    
    def convert_to_grayscale(self) -> None:
        """转换为灰度图"""
        if self.image is None:
            raise ValueError("没有加载图像")
        
        if len(self.image.shape) == 3:
            gray = cv2.cvtColor(self.image, cv2.COLOR_RGB2GRAY)
            self.image = gray
            self.metadata['channels'] = 1
            self._save_state("grayscale")
    
    def rotate(self, angle: float, expand: bool = True) -> None:
        """旋转图像"""
        if self.image is None:
            raise ValueError("没有加载图像")
        
        height, width = self.image.shape[:2]
        center = (width / 2, height / 2)
        
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        
        if expand:
            cos = np.abs(M[0, 0])
            sin = np.abs(M[0, 1])
            new_width = int((height * sin) + (width * cos))
            new_height = int((height * cos) + (width * sin))
            
            M[0, 2] += (new_width / 2) - center[0]
            M[1, 2] += (new_height / 2) - center[1]
            
            rotated = cv2.warpAffine(self.image, M, (new_width, new_height))
        else:
            rotated = cv2.warpAffine(self.image, M, (width, height))
        
        self.image = rotated
        self._save_state(f"rotate_{angle}")
    
    def crop(self, left: int, top: int, right: int, bottom: int) -> None:
        """裁剪图像"""
        if self.image is None:
            raise ValueError("没有加载图像")
        
        height, width = self.image.shape[:2]
        
        if left < 0 or top < 0 or right > width or bottom > height:
            raise ValueError("裁剪区域超出图像边界")
        
        if left >= right or top >= bottom:
            raise ValueError("无效的裁剪区域")
        
        cropped = self.image[top:bottom, left:right]
        self.image = cropped
        
        self.metadata['width'] = right - left
        self.metadata['height'] = bottom - top
        self._save_state("crop")
    
    def adjust_brightness(self, factor: float) -> None:
        """调整亮度"""
        if self.image is None:
            raise ValueError("没有加载图像")
        
        if factor < 0:
            raise ValueError("亮度因子必须非负")
        
        if self.image.dtype != np.uint8:
            self.image = self.image.astype(np.uint8)
        
        adjusted = np.clip(self.image.astype(np.float32) * factor, 0, 255).astype(np.uint8)
        self.image = adjusted
        self._save_state(f"brightness_{factor}")
    
    def adjust_contrast(self, factor: float) -> None:
        """调整对比度"""
        if self.image is None:
            raise ValueError("没有加载图像")
        
        if self.image.dtype != np.uint8:
            self.image = self.image.astype(np.uint8)
        
        mean = np.mean(self.image, dtype=np.float32)
        adjusted = np.clip((self.image.astype(np.float32) - mean) * factor + mean, 0, 255).astype(np.uint8)
        self.image = adjusted
        self._save_state(f"contrast_{factor}")
    
    def get_histogram(self, bins: int = 256) -> Dict[str, np.ndarray]:
        """获取图像直方图"""
        if self.image is None:
            raise ValueError("没有加载图像")
        
        histograms = {}
        
        if len(self.image.shape) == 2:
            hist, _ = np.histogram(self.image.flatten(), bins=bins, range=[0, 256])
            histograms['gray'] = hist
        else:
            for i, channel in enumerate(['red', 'green', 'blue']):
                hist, _ = np.histogram(self.image[:, :, i].flatten(), bins=bins, range=[0, 256])
                histograms[channel] = hist
        
        return histograms
    
    def normalize(self) -> None:
        """归一化图像"""
        if self.image is None:
            raise ValueError("没有加载图像")
        
        min_val = np.min(self.image)
        max_val = np.max(self.image)
        
        if max_val - min_val == 0:
            return
        
        normalized = ((self.image - min_val) / (max_val - min_val) * 255).astype(np.uint8)
        self.image = normalized
        self._save_state("normalize")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取图像统计信息"""
        if self.image is None:
            raise ValueError("没有加载图像")
        
        return {
            'mean': float(np.mean(self.image)),
            'std': float(np.std(self.image)),
            'min': float(np.min(self.image)),
            'max': float(np.max(self.image)),
            'median': float(np.median(self.image))
        }
