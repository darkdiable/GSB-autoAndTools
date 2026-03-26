"""
ImageCraft 测试套件
包含多个测试用例，用于验证和调试
"""

import numpy as np
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.processor import ImageProcessor
from core.pipeline import ProcessingPipeline
from filters import blur, edge_detection, enhance
from utils import image_utils, color_utils, transform
from io import image_io


def create_test_image(width: int = 256, height: int = 256) -> np.ndarray:
    """创建测试图像"""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    for i in range(height):
        for j in range(width):
            img[i, j, 0] = int(255 * i / height)
            img[i, j, 1] = int(255 * j / width)
            img[i, j, 2] = 128
    
    return img


def test_processor_basic():
    """测试处理器基本功能"""
    print("测试处理器基本功能...")
    
    processor = ImageProcessor()
    test_img = create_test_image()
    processor.image = test_img
    processor.original_image = test_img.copy()
    processor.metadata = {
        'width': test_img.shape[1],
        'height': test_img.shape[0],
        'channels': 3
    }
    
    processor.adjust_brightness(1.2)
    processor.adjust_contrast(1.1)
    
    stats = processor.get_statistics()
    print(f"  统计信息：{stats}")
    
    print("  ✓ 处理器基本功能测试完成")


def test_filters():
    """测试滤镜功能"""
    print("测试滤镜功能...")
    
    test_img = create_test_image()
    
    blurred = blur.gaussian_blur(test_img, sigma=2.0)
    print(f"  高斯模糊完成：{blurred.shape}")
    
    edges = edge_detection.sobel_edge(test_img)
    print(f"  Sobel 边缘检测完成：{edges.shape}")
    
    sharpened = enhance.sharpen(test_img, alpha=1.5)
    print(f"  锐化完成：{sharpened.shape}")
    
    print("  ✓ 滤镜功能测试完成")


def test_color_conversion():
    """测试颜色空间转换"""
    print("测试颜色空间转换...")
    
    test_img = create_test_image()
    
    gray = color_utils.rgb_to_grayscale(test_img)
    print(f"  RGB 转灰度完成：{gray.shape}")
    
    hsv = color_utils.rgb_to_hsv(test_img)
    print(f"  RGB 转 HSV 完成：{hsv.shape}")
    
    lab = color_utils.rgb_to_lab(test_img)
    print(f"  RGB 转 LAB 完成：{lab.shape}")
    
    print("  ✓ 颜色空间转换测试完成")


def test_transforms():
    """测试变换功能"""
    print("测试变换功能...")
    
    test_img = create_test_image()
    
    aff = transform.AffineTransform()
    rotated = aff.rotate(test_img, 45)
    print(f"  旋转完成：{rotated.shape}")
    
    translated = aff.translate(test_img, 10, 20)
    print(f"  平移完成：{translated.shape}")
    
    persp = transform.PerspectiveTransform()
    flipped = persp.flip(test_img, 'horizontal')
    print(f"  翻转完成：{flipped.shape}")
    
    print("  ✓ 变换功能测试完成")


def test_utils():
    """测试工具函数"""
    print("测试工具函数...")
    
    img1 = create_test_image()
    img2 = create_test_image(128, 128)
    
    psnr = image_utils.calculate_psnr(img1, img1)
    print(f"  PSNR (相同图像): {psnr}")
    
    ssim = image_utils.calculate_ssim(img1, img1)
    print(f"  SSIM (相同图像): {ssim}")
    
    resized = image_utils.resize_image(img1, 0.5)
    print(f"  缩放完成：{resized.shape}")
    
    print("  ✓ 工具函数测试完成")


def test_pipeline():
    """测试流水线"""
    print("测试流水线...")
    
    pipeline = ProcessingPipeline()
    
    def dummy_op(image=None):
        pass
    
    pipeline.add_step(dummy_op)
    
    is_valid = pipeline.validate()
    print(f"  流水线验证：{is_valid}")
    
    print("  ✓ 流水线测试完成")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("ImageCraft 测试套件")
    print("=" * 50)
    
    try:
        test_processor_basic()
        test_filters()
        test_color_conversion()
        test_transforms()
        test_utils()
        test_pipeline()
        
        print("=" * 50)
        print("所有测试完成!")
        print("=" * 50)
        
    except Exception as e:
        print(f"\n❌ 测试失败：{e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    run_all_tests()
