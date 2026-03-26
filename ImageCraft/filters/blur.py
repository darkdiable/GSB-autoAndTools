import numpy as np
import cv2
from scipy import ndimage


def gaussian_blur(image: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    """
    高斯模糊
    
    Args:
        image: 输入图像
        sigma: 高斯核的标准差
    
    Returns:
        模糊后的图像
    """
    if len(image.shape) == 2:
        blurred = ndimage.gaussian_filter(image, sigma=sigma)
    else:
        blurred = np.zeros_like(image)
        for i in range(image.shape[2]):
            blurred[:, :, i] = ndimage.gaussian_filter(image[:, :, i], sigma=sigma)
    
    return np.clip(blurred, 0, 255).astype(np.uint8)


def median_blur(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """
    中值滤波
    
    Args:
        image: 输入图像
        kernel_size: 滤波核大小（必须为奇数）
    
    Returns:
        滤波后的图像
    """
    if kernel_size % 2 == 0:
        kernel_size += 1
    
    if kernel_size < 1:
        kernel_size = 3
    
    if len(image.shape) == 2:
        filtered = cv2.medianBlur(image, kernel_size)
    else:
        filtered = np.zeros_like(image)
        for i in range(image.shape[2]):
            filtered[:, :, i] = cv2.medianBlur(image[:, :, i], kernel_size)
    
    return filtered


def bilateral_filter(image: np.ndarray, d: int = 9, sigma_color: float = 75, sigma_space: float = 75) -> np.ndarray:
    """
    双边滤波（保边滤波）
    
    Args:
        image: 输入图像
        d: 邻域直径
        sigma_color: 颜色空间标准差
        sigma_space: 坐标空间标准差
    
    Returns:
        滤波后的图像
    """
    if d <= 0:
        d = 9
    
    if sigma_color <= 0:
        sigma_color = 75
    
    if sigma_space <= 0:
        sigma_space = 75
    
    filtered = cv2.bilateralFilter(image, d, sigma_color, sigma_space)
    
    return filtered


def box_blur(image: np.ndarray, kernel_size: int = 3) -> np.ndarray:
    """
    盒式滤波
    
    Args:
        image: 输入图像
        kernel_size: 滤波核大小
    
    Returns:
        滤波后的图像
    """
    kernel = np.ones((kernel_size, kernel_size)) / (kernel_size * kernel_size)
    
    if len(image.shape) == 2:
        filtered = ndimage.convolve(image, kernel)
    else:
        filtered = np.zeros_like(image)
        for i in range(image.shape[2]):
            filtered[:, :, i] = ndimage.convolve(image[:, :, i], kernel)
    
    return np.clip(filtered, 0, 255).astype(np.uint8)


def motion_blur(image: np.ndarray, kernel_size: int = 9, angle: float = 0) -> np.ndarray:
    """
    运动模糊
    
    Args:
        image: 输入图像
        kernel_size: 模糊核大小
        angle: 模糊方向角度（度）
    
    Returns:
        模糊后的图像
    """
    kernel = np.zeros((kernel_size, kernel_size))
    center = kernel_size // 2
    
    for i in range(kernel_size):
        x = center + (i - center) * np.cos(np.radians(angle))
        y = center + (i - center) * np.sin(np.radians(angle))
        
        x0, y0 = int(np.round(x)), int(np.round(y))
        
        if 0 <= x0 < kernel_size and 0 <= y0 < kernel_size:
            kernel[y0, x0] += 1
    
    kernel = kernel / np.sum(kernel)
    
    if len(image.shape) == 2:
        filtered = ndimage.convolve(image, kernel, mode='reflect')
    else:
        filtered = np.zeros_like(image)
        for i in range(image.shape[2]):
            filtered[:, :, i] = ndimage.convolve(image[:, :, i], kernel, mode='reflect')
    
    return np.clip(filtered, 0, 255).astype(np.uint8)
