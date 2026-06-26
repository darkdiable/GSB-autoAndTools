import numpy as np
from typing import Tuple, List, Optional
import cv2


class ImageUtils:
    """图像工具类"""
    
    @staticmethod
    def pad_image(image: np.ndarray, padding: int, mode: str = 'constant') -> np.ndarray:
        """
        填充图像边界
        
        Args:
            image: 输入图像
            padding: 填充大小
            mode: 填充模式
        
        Returns:
            填充后的图像
        """
        if len(image.shape) == 2:
            padded = np.pad(image, padding, mode=mode)
        else:
            padded = np.pad(image, ((padding, padding), (padding, padding), (0, 0)), mode=mode)
        
        return padded
    
    @staticmethod
    def tile_images(images: List[np.ndarray], rows: int, cols: int) -> np.ndarray:
        """
        将多个图像拼接成网格
        
        Args:
            images: 图像列表
            rows: 行数
            cols: 列数
        
        Returns:
            拼接后的图像
        """
        if len(images) != rows * cols:
            raise ValueError(f"图像数量 {len(images)} 不匹配 {rows}x{cols} 网格")
        
        max_height = max(img.shape[0] for img in images)
        max_width = max(img.shape[1] for img in images)
        
        if len(images[0].shape) == 2:
            tiled = np.zeros((rows * max_height, cols * max_width), dtype=images[0].dtype)
        else:
            channels = images[0].shape[2]
            tiled = np.zeros((rows * max_height, cols * max_width, channels), dtype=images[0].dtype)
        
        for idx, img in enumerate(images):
            i = idx // cols
            j = idx % cols
            
            y_start = i * max_height
            x_start = j * max_width
            
            if len(img.shape) == 2:
                tiled[y_start:y_start+img.shape[0], x_start:x_start+img.shape[1]] = img
            else:
                tiled[y_start:y_start+img.shape[0], x_start:x_start+img.shape[1], :] = img
        
        return tiled
    
    @staticmethod
    def split_channels(image: np.ndarray) -> List[np.ndarray]:
        """
        分离图像通道
        
        Args:
            image: 输入图像
        
        Returns:
            通道列表
        """
        if len(image.shape) == 2:
            return [image]
        
        channels = []
        for i in range(image.shape[2]):
            channels.append(image[:, :, i])
        
        return channels
    
    @staticmethod
    def merge_channels(channels: List[np.ndarray]) -> np.ndarray:
        """
        合并通道
        
        Args:
            channels: 通道列表
        
        Returns:
            合并后的图像
        """
        if len(channels) == 1:
            return channels[0]
        
        return np.stack(channels, axis=2)
    
    @staticmethod
    def resize_image(image: np.ndarray, scale: float) -> np.ndarray:
        """
        缩放图像
        
        Args:
            image: 输入图像
            scale: 缩放比例
        
        Returns:
            缩放后的图像
        """
        if scale <= 0:
            raise ValueError("缩放比例必须为正数")
        
        new_height = int(image.shape[0] * scale)
        new_width = int(image.shape[1] * scale)
        
        resized = cv2.resize(image, (new_width, new_height))
        
        return resized
    
    @staticmethod
    def get_image_size(image: np.ndarray) -> Tuple[int, int]:
        """
        获取图像尺寸
        
        Args:
            image: 输入图像
        
        Returns:
            (宽度，高度) 元组
        """
        if len(image.shape) == 2:
            return (image.shape[1], image.shape[0])
        else:
            return (image.shape[1], image.shape[0])
    
    @staticmethod
    def create_blank_image(width: int, height: int, color: Tuple[int, ...] = (255, 255, 255)) -> np.ndarray:
        """
        创建空白图像
        
        Args:
            width: 宽度
            height: 高度
            color: 背景颜色
        
        Returns:
            空白图像
        """
        if len(color) == 1:
            img = np.zeros((height, width), dtype=np.uint8)
            img[:] = color[0]
        else:
            img = np.zeros((height, width, len(color)), dtype=np.uint8)
            for i, c in enumerate(color):
                img[:, :, i] = c
        
        return img


def calculate_psnr(original: np.ndarray, processed: np.ndarray) -> float:
    """
    计算峰值信噪比 (PSNR)
    
    Args:
        original: 原始图像
        processed: 处理后的图像
    
    Returns:
        PSNR 值
    """
    if original.shape != processed.shape:
        raise ValueError("输入图像形状必须相同")
    
    mse = np.mean((original.astype(np.float64) - processed.astype(np.float64)) ** 2)
    
    if mse == 0:
        return float('inf')
    
    max_pixel = 255.0
    psnr = 10 * np.log10((max_pixel ** 2) / mse)
    
    return psnr


def calculate_ssim(img1: np.ndarray, img2: np.ndarray) -> float:
    """
    计算结构相似性指数 (SSIM)
    
    Args:
        img1: 图像 1
        img2: 图像 2
    
    Returns:
        SSIM 值
    """
    C1 = (0.01 * 255) ** 2
    C2 = (0.03 * 255) ** 2
    
    if img1.shape != img2.shape:
        raise ValueError("输入图像形状必须相同")
    
    if len(img1.shape) == 3:
        img1 = cv2.cvtColor(img1, cv2.COLOR_RGB2GRAY)
        img2 = cv2.cvtColor(img2, cv2.COLOR_RGB2GRAY)
    
    img1 = img1.astype(np.float64)
    img2 = img2.astype(np.float64)
    
    mu1 = cv2.GaussianBlur(img1, (11, 11), 1.5)
    mu2 = cv2.GaussianBlur(img2, (11, 11), 1.5)
    
    mu1_sq = mu1 ** 2
    mu2_sq = mu2 ** 2
    mu1_mu2 = mu1 * mu2
    
    sigma1_sq = cv2.GaussianBlur(img1 ** 2, (11, 11), 1.5) - mu1_sq
    sigma2_sq = cv2.GaussianBlur(img2 ** 2, (11, 11), 1.5) - mu2_sq
    sigma12 = cv2.GaussianBlur(img1 * img2, (11, 11), 1.5) - mu1_mu2
    
    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / \
               ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))
    
    return float(np.mean(ssim_map))


def calculate_histogram(image: np.ndarray, bins: int = 256) -> np.ndarray:
    """
    计算图像直方图
    
    Args:
        image: 输入图像
        bins: 直方图 bin 数量
    
    Returns:
        直方图数组
    """
    if len(image.shape) == 2:
        hist, _ = np.histogram(image.flatten(), bins=bins, range=[0, 256])
    else:
        hist = np.zeros(bins)
        for i in range(image.shape[2]):
            channel_hist, _ = np.histogram(image[:, :, i].flatten(), bins=bins, range=[0, 256])
            hist += channel_hist
    
    return hist


def equalize_histogram(image: np.ndarray) -> np.ndarray:
    """
    直方图均衡化
    
    Args:
        image: 输入图像
    
    Returns:
        均衡化后的图像
    """
    if len(image.shape) == 2:
        equalized = cv2.equalizeHist(image)
    else:
        equalized = np.zeros_like(image)
        for i in range(image.shape[2]):
            equalized[:, :, i] = cv2.equalizeHist(image[:, :, i])
    
    return equalized


# 模块级别的便捷函数
def resize_image(image: np.ndarray, scale: float) -> np.ndarray:
    """缩放图像的便捷函数"""
    return ImageUtils.resize_image(image, scale)
