import numpy as np
from typing import Tuple, Optional
import cv2


class ColorConverter:
    """颜色空间转换器"""
    
    @staticmethod
    def rgb_to_grayscale(image: np.ndarray) -> np.ndarray:
        """
        RGB 转灰度
        
        Args:
            image: RGB 图像
        
        Returns:
            灰度图像
        """
        if len(image.shape) == 2:
            return image
        
        gray = np.dot(image[..., :3], [0.299, 0.587, 0.114])
        return gray.astype(np.uint8)
    
    @staticmethod
    def rgb_to_hsv(image: np.ndarray) -> np.ndarray:
        """
        RGB 转 HSV
        
        Args:
            image: RGB 图像
        
        Returns:
            HSV 图像
        """
        if len(image.shape) == 2:
            return image
        
        hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
        return hsv
    
    @staticmethod
    def hsv_to_rgb(image: np.ndarray) -> np.ndarray:
        """
        HSV 转 RGB
        
        Args:
            image: HSV 图像
        
        Returns:
            RGB 图像
        """
        if len(image.shape) == 2:
            return image
        
        rgb = cv2.cvtColor(image, cv2.COLOR_HSV2RGB)
        return rgb
    
    @staticmethod
    def rgb_to_lab(image: np.ndarray) -> np.ndarray:
        """
        RGB 转 LAB
        
        Args:
            image: RGB 图像
        
        Returns:
            LAB 图像
        """
        if len(image.shape) == 2:
            return image
        
        lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)
        return lab
    
    @staticmethod
    def lab_to_rgb(image: np.ndarray) -> np.ndarray:
        """
        LAB 转 RGB
        
        Args:
            image: LAB 图像
        
        Returns:
            RGB 图像
        """
        if len(image.shape) == 2:
            return image
        
        rgb = cv2.cvtColor(image, cv2.COLOR_LAB2RGB)
        return rgb
    
    @staticmethod
    def rgb_to_ycbcr(image: np.ndarray) -> np.ndarray:
        """
        RGB 转 YCbCr
        
        Args:
            image: RGB 图像
        
        Returns:
            YCbCr 图像
        """
        if len(image.shape) == 2:
            return image
        
        ycbcr = cv2.cvtColor(image, cv2.COLOR_RGB2YCrCb)
        return ycbcr
    
    @staticmethod
    def ycbcr_to_rgb(image: np.ndarray) -> np.ndarray:
        """
        YCbCr 转 RGB
        
        Args:
            image: YCbCr 图像
        
        Returns:
            RGB 图像
        """
        if len(image.shape) == 2:
            return image
        
        rgb = cv2.cvtColor(image, cv2.COLOR_YCrCb2RGB)
        return rgb


def color_transfer(source: np.ndarray, target: np.ndarray) -> np.ndarray:
    """
    颜色迁移：将目标图像的颜色风格迁移到源图像
    
    Args:
        source: 源图像
        target: 目标图像
    
    Returns:
        颜色迁移后的图像
    """
    source_lab = cv2.cvtColor(source, cv2.COLOR_RGB2LAB).astype("float32")
    target_lab = cv2.cvtColor(target, cv2.COLOR_RGB2LAB).astype("float32")
    
    (source_l, source_a, source_b) = cv2.split(source_lab)
    (target_l, target_a, target_b) = cv2.split(target_lab)
    
    (l_mean, l_std) = (source_l.mean(), source_l.std())
    (a_mean, a_std) = (source_a.mean(), source_a.std())
    (b_mean, b_std) = (source_b.mean(), source_b.std())
    
    (target_l_mean, target_l_std) = (target_l.mean(), target_l.std())
    (target_a_mean, target_a_std) = (target_a.mean(), target_a.std())
    (target_b_mean, target_b_std) = (target_b.mean(), target_b.std())
    
    target_l = (target_l - target_l_mean) * (l_std / (target_l_std + 1e-6)) + l_mean
    target_a = (target_a - target_a_mean) * (a_std / (target_a_std + 1e-6)) + a_mean
    target_b = (target_b - target_b_mean) * (b_std / (target_b_std + 1e-6)) + b_mean
    
    target_l = np.clip(target_l, 0, 255)
    target_a = np.clip(target_a, 0, 255)
    target_b = np.clip(target_b, 0, 255)
    
    transferred = cv2.merge([target_l, target_a, target_b])
    transferred = cv2.cvtColor(transferred.astype("uint8"), cv2.COLOR_LAB2RGB)
    
    return transferred


def adjust_saturation(image: np.ndarray, factor: float) -> np.ndarray:
    """
    调整饱和度
    
    Args:
        image: RGB 图像
        factor: 饱和度因子（<1 降低，>1 增强）
    
    Returns:
        调整后的图像
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    h, s, v = cv2.split(hsv)
    
    s = np.clip(s * factor, 0, 255).astype(np.uint8)
    
    hsv = cv2.merge([h, s, v])
    adjusted = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    
    return adjusted


def adjust_hue(image: np.ndarray, angle: float) -> np.ndarray:
    """
    调整色调
    
    Args:
        image: RGB 图像
        angle: 色调旋转角度（0-360）
    
    Returns:
        调整后的图像
    """
    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    h, s, v = cv2.split(hsv)
    
    h = (h + angle / 2) % 180
    
    hsv = cv2.merge([h, s, v])
    adjusted = cv2.cvtColor(hsv, cv2.COLOR_HSV2RGB)
    
    return adjusted


def invert_colors(image: np.ndarray) -> np.ndarray:
    """
    反色
    
    Args:
        image: 输入图像
    
    Returns:
        反色后的图像
    """
    return 255 - image


def posterize(image: np.ndarray, bits: int = 4) -> np.ndarray:
    """
    色调分离
    
    Args:
        image: 输入图像
        bits: 每个通道的位数（1-8）
    
    Returns:
        色调分离后的图像
    """
    if bits < 1 or bits > 8:
        raise ValueError("bits 必须在 1-8 之间")
    
    levels = 2 ** bits
    step = 256 // levels
    
    posterized = (image // step) * step
    
    return posterized


# 模块级别的便捷函数
def rgb_to_grayscale(image: np.ndarray) -> np.ndarray:
    """RGB 转灰度的便捷函数"""
    return ColorConverter.rgb_to_grayscale(image)


def rgb_to_hsv(image: np.ndarray) -> np.ndarray:
    """RGB 转 HSV 的便捷函数"""
    return ColorConverter.rgb_to_hsv(image)


def rgb_to_lab(image: np.ndarray) -> np.ndarray:
    """RGB 转 LAB 的便捷函数"""
    return ColorConverter.rgb_to_lab(image)
