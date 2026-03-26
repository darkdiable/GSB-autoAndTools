import numpy as np
from scipy import ndimage


def sharpen(image: np.ndarray, alpha: float = 1.5) -> np.ndarray:
    """
    锐化滤镜
    
    Args:
        image: 输入图像
        alpha: 锐化强度
    
    Returns:
        锐化后的图像
    """
    if image.dtype != np.float32:
        image = image.astype(np.float32)
    
    blur = ndimage.gaussian_filter(image, sigma=3)
    
    sharpened = image + alpha * (image - blur)
    
    return np.clip(sharpened, 0, 255).astype(np.uint8)


def emboss(image: np.ndarray, angle: float = 135) -> np.ndarray:
    """
    浮雕滤镜
    
    Args:
        image: 输入图像
        angle: 浮雕角度
    
    Returns:
        浮雕效果图像
    """
    rad = np.radians(angle)
    
    kernel = np.array([
        [-2, -1, 0],
        [-1, 1, 1],
        [0, 1, 2]
    ])
    
    if len(image.shape) == 2:
        embossed = ndimage.convolve(image, kernel)
        embossed = embossed + 128
    else:
        embossed = np.zeros_like(image)
        for i in range(image.shape[2]):
            embossed[:, :, i] = ndimage.convolve(image[:, :, i], kernel)
            embossed[:, :, i] = embossed[:, :, i] + 128
    
    return np.clip(embossed, 0, 255).astype(np.uint8)


def outline(image: np.ndarray, threshold: int = 128) -> np.ndarray:
    """
    轮廓滤镜
    
    Args:
        image: 输入图像
        threshold: 二值化阈值
    
    Returns:
        轮廓图像
    """
    if len(image.shape) == 3:
        import cv2
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    
    _, binary = cv2.threshold(gray, threshold, 255, cv2.THRESH_BINARY)
    
    kernel = np.ones((3, 3), dtype=np.uint8)
    
    eroded = cv2.erode(binary, kernel, iterations=1)
    
    outline_img = cv2.subtract(binary, eroded)
    
    if len(image.shape) == 3:
        outline_img = cv2.cvtColor(outline_img, cv2.COLOR_GRAY2RGB)
    
    return outline_img


def sketch(image: np.ndarray) -> np.ndarray:
    """
    素描滤镜
    
    Args:
        image: 输入图像
    
    Returns:
        素描效果图像
    """
    import cv2
    
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        gray = image
    
    inverted = 255 - gray
    
    blurred = ndimage.gaussian_filter(inverted, sigma=5)
    
    sketch_img = np.zeros_like(gray)
    mask = blurred > 0
    sketch_img[mask] = np.minimum(255, gray[mask] * 255 / blurred[mask])
    
    if len(image.shape) == 3:
        sketch_img = cv2.cvtColor(sketch_img, cv2.COLOR_GRAY2RGB)
    
    return sketch_img


def cartoon(image: np.ndarray) -> np.ndarray:
    """
    卡通化滤镜
    
    Args:
        image: 输入图像
    
    Returns:
        卡通化图像
    """
    import cv2
    
    if len(image.shape) == 3:
        color = cv2.bilateralFilter(image, 9, 75, 75)
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)
    else:
        color = cv2.bilateralFilter(image, 9, 75, 75)
        gray = color
    
    edges = cv2.adaptiveThreshold(
        gray, 255,
        cv2.ADAPTIVE_THRESH_MEAN_C,
        cv2.THRESH_BINARY,
        9,
        2
    )
    
    if len(image.shape) == 3:
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2RGB)
        cartoonized = cv2.bitwise_and(color, edges)
    else:
        cartoonized = cv2.bitwise_and(color, edges)
    
    return cartoonized
