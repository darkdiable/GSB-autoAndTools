import numpy as np
import cv2
from scipy import ndimage


def sobel_edge(image: np.ndarray, direction: str = 'both') -> np.ndarray:
    """
    Sobel 边缘检测
    
    Args:
        image: 输入图像（可以是灰度或彩色）
        direction: 边缘检测方向 ('x', 'y', 'both')
    
    Returns:
        边缘图像
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    
    if gray.dtype != np.uint8:
        gray = np.clip(gray, 0, 255).astype(np.uint8)
    
    if direction == 'x':
        edges = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    elif direction == 'y':
        edges = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    else:
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        edges = np.sqrt(sobel_x**2 + sobel_y**2)
    
    edges = np.abs(edges)
    edges = np.clip(edges, 0, 255).astype(np.uint8)
    
    if len(image.shape) == 3:
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    
    return edges


def canny_edge(image: np.ndarray, threshold1: int = 100, threshold2: int = 200) -> np.ndarray:
    """
    Canny 边缘检测
    
    Args:
        image: 输入图像
        threshold1: 第一阈值
        threshold2: 第二阈值
    
    Returns:
        边缘图像
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    
    edges = cv2.Canny(gray, threshold1, threshold2)
    
    if len(image.shape) == 3:
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    
    return edges


def laplacian_edge(image: np.ndarray) -> np.ndarray:
    """
    Laplacian 边缘检测
    
    Args:
        image: 输入图像
    
    Returns:
        边缘图像
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    
    edges = cv2.Laplacian(gray, cv2.CV_64F)
    edges = np.abs(edges)
    edges = np.clip(edges, 0, 255).astype(np.uint8)
    
    if len(image.shape) == 3:
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    
    return edges


def prewitt_edge(image: np.ndarray) -> np.ndarray:
    """
    Prewitt 边缘检测
    
    Args:
        image: 输入图像
    
    Returns:
        边缘图像
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    
    kernel_x = np.array([[-1, 0, 1], [-1, 0, 1], [-1, 0, 1]])
    kernel_y = np.array([[-1, -1, -1], [0, 0, 0], [1, 1, 1]])
    
    edge_x = ndimage.convolve(gray, kernel_x)
    edge_y = ndimage.convolve(gray, kernel_y)
    
    edges = np.sqrt(edge_x**2 + edge_y**2)
    edges = np.clip(edges, 0, 255).astype(np.uint8)
    
    if len(image.shape) == 3:
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    
    return edges


def roberts_edge(image: np.ndarray) -> np.ndarray:
    """
    Roberts 边缘检测
    
    Args:
        image: 输入图像
    
    Returns:
        边缘图像
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    
    kernel_x = np.array([[1, 0], [0, -1]])
    kernel_y = np.array([[0, 1], [-1, 0]])
    
    edge_x = ndimage.convolve(gray, kernel_x)
    edge_y = ndimage.convolve(gray, kernel_y)
    
    edges = np.sqrt(edge_x**2 + edge_y**2)
    edges = np.clip(edges, 0, 255).astype(np.uint8)
    
    if len(image.shape) == 3:
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
    
    return edges
