import numpy as np
from typing import Tuple, Optional
import cv2


class AffineTransform:
    """仿射变换类"""
    
    def __init__(self):
        self.matrix: Optional[np.ndarray] = None
    
    def translate(self, image: np.ndarray, tx: int, ty: int) -> np.ndarray:
        """
        平移变换
        
        Args:
            image: 输入图像
            tx: x 方向平移量
            ty: y 方向平移量
        
        Returns:
            平移后的图像
        """
        height, width = image.shape[:2]
        
        M = np.float32([
            [1, 0, tx],
            [0, 1, ty]
        ])
        
        translated = cv2.warpAffine(image, M, (width, height))
        
        return translated
    
    def scale(self, image: np.ndarray, sx: float, sy: float) -> np.ndarray:
        """
        缩放变换
        
        Args:
            image: 输入图像
            sx: x 方向缩放比例
            sy: y 方向缩放比例
        
        Returns:
            缩放后的图像
        """
        height, width = image.shape[:2]
        
        M = np.float32([
            [sx, 0, 0],
            [0, sy, 0]
        ])
        
        new_width = int(width * sx)
        new_height = int(height * sy)
        
        if new_width <= 0 or new_height <= 0:
            raise ValueError("缩放后的尺寸必须为正数")
        
        scaled = cv2.warpAffine(image, M, (new_width, new_height), flags=cv2.INTER_LINEAR)
        
        return scaled
    
    def rotate(self, image: np.ndarray, angle: float, scale: float = 1.0) -> np.ndarray:
        """
        旋转变换
        
        Args:
            image: 输入图像
            angle: 旋转角度（逆时针）
            scale: 缩放比例
        
        Returns:
            旋转后的图像
        """
        height, width = image.shape[:2]
        center = (width / 2, height / 2)
        
        M = cv2.getRotationMatrix2D(center, angle, scale)
        
        rotated = cv2.warpAffine(image, M, (width, height))
        
        return rotated
    
    def shear(self, image: np.ndarray, shear_x: float = 0, shear_y: float = 0) -> np.ndarray:
        """
        剪切变换
        
        Args:
            image: 输入图像
            shear_x: x 方向剪切因子
            shear_y: y 方向剪切因子
        
        Returns:
            剪切后的图像
        """
        height, width = image.shape[:2]
        
        M = np.float32([
            [1, shear_x, 0],
            [shear_y, 1, 0]
        ])
        
        sheared = cv2.warpAffine(image, M, (width, height))
        
        return sheared
    
    def compose(self, image: np.ndarray, matrix: np.ndarray) -> np.ndarray:
        """
        应用自定义仿射变换矩阵
        
        Args:
            image: 输入图像
            matrix: 2x3 仿射变换矩阵
        
        Returns:
            变换后的图像
        """
        height, width = image.shape[:2]
        
        transformed = cv2.warpAffine(image, matrix, (width, height))
        
        return transformed


class PerspectiveTransform:
    """透视变换类"""
    
    def __init__(self):
        self.matrix: Optional[np.ndarray] = None
    
    def transform(self, image: np.ndarray, src_points: np.ndarray, dst_points: np.ndarray) -> np.ndarray:
        """
        应用透视变换
        
        Args:
            image: 输入图像
            src_points: 源点坐标 (4x2)
            dst_points: 目标点坐标 (4x2)
        
        Returns:
            变换后的图像
        """
        src = src_points.astype(np.float32)
        dst = dst_points.astype(np.float32)
        
        M = cv2.getPerspectiveTransform(src, dst)
        
        height, width = image.shape[:2]
        
        transformed = cv2.warpPerspective(image, M, (width, height))
        
        self.matrix = M
        
        return transformed
    
    def rotate_3d(self, image: np.ndarray, angle_x: float, angle_y: float, angle_z: float) -> np.ndarray:
        """
        3D 旋转（模拟）
        
        Args:
            image: 输入图像
            angle_x: x 轴旋转角度
            angle_y: y 轴旋转角度
            angle_z: z 轴旋转角度
        
        Returns:
            变换后的图像
        """
        height, width = image.shape[:2]
        
        src_points = np.float32([
            [0, 0],
            [width, 0],
            [width, height],
            [0, height]
        ])
        
        theta_x = np.radians(angle_x)
        theta_y = np.radians(angle_y)
        theta_z = np.radians(angle_z)
        
        scale_x = np.cos(theta_y)
        scale_y = np.cos(theta_x)
        
        dst_points = np.float32([
            [width * 0.1, height * 0.1],
            [width * 0.9, height * 0.05],
            [width * 0.95, height * 0.95],
            [width * 0.05, height * 0.9]
        ])
        
        return self.transform(image, src_points, dst_points)
    
    def flip(self, image: np.ndarray, mode: str = 'horizontal') -> np.ndarray:
        """
        翻转图像
        
        Args:
            image: 输入图像
            mode: 翻转模式 ('horizontal', 'vertical', 'both')
        
        Returns:
            翻转后的图像
        """
        if mode == 'horizontal':
            return cv2.flip(image, 1)
        elif mode == 'vertical':
            return cv2.flip(image, 0)
        elif mode == 'both':
            return cv2.flip(image, -1)
        else:
            raise ValueError(f"未知的翻转模式：{mode}")
