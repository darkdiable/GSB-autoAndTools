"""
测试图像生成器
生成用于测试的示例图像
"""

import numpy as np
import cv2
import os


def generate_gradient_image(width: int = 512, height: int = 512) -> np.ndarray:
    """生成渐变测试图像"""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    for i in range(height):
        for j in range(width):
            img[i, j, 0] = int(255 * i / height)
            img[i, j, 1] = int(255 * j / width)
            img[i, j, 2] = int(255 * (i + j) / (height + width))
    
    return img


def generate_checkerboard(width: int = 512, height: int = 512, 
                         square_size: int = 32) -> np.ndarray:
    """生成棋盘格测试图像"""
    img = np.ones((height, width, 3), dtype=np.uint8) * 255
    
    for i in range(height):
        for j in range(width):
            if ((i // square_size) + (j // square_size)) % 2 == 0:
                img[i, j] = [0, 0, 0]
    
    return img


def generate_color_bars(width: int = 512, height: int = 512) -> np.ndarray:
    """生成彩色条纹测试图像"""
    img = np.zeros((height, width, 3), dtype=np.uint8)
    
    colors = [
        (255, 255, 255),
        (255, 0, 0),
        (0, 255, 0),
        (0, 0, 255),
        (255, 255, 0),
        (0, 255, 255),
        (255, 0, 255),
        (0, 0, 0)
    ]
    
    bar_width = width // len(colors)
    
    for i, color in enumerate(colors):
        img[:, i * bar_width:(i + 1) * bar_width] = color
    
    return img


def generate_shapes(width: int = 512, height: int = 512) -> np.ndarray:
    """生成几何形状测试图像"""
    img = np.ones((height, width, 3), dtype=np.uint8) * 240
    
    cv2.rectangle(img, (50, 50), (200, 200), (255, 0, 0), -1)
    cv2.circle(img, (350, 150), 80, (0, 255, 0), -1)
    cv2.ellipse(img, (150, 350), (100, 60), 45, 0, 360, (0, 0, 255), -1)
    pts = np.array([[350, 250], [450, 450], [250, 450]], np.int32)
    cv2.fillPoly(img, [pts], (255, 255, 0))
    
    return img


def generate_noise_image(width: int = 512, height: int = 512, 
                        noise_level: int = 50) -> np.ndarray:
    """生成带噪声的测试图像"""
    img = np.random.randint(100, 150, (height, width, 3), dtype=np.uint8)
    
    noise = np.random.randint(-noise_level, noise_level, 
                             (height, width, 3), dtype=np.int16)
    img = np.clip(img.astype(np.int16) + noise, 0, 255).astype(np.uint8)
    
    return img


def main():
    """生成所有测试图像"""
    output_dir = 'test_images'
    
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    print("生成测试图像...")
    
    gradient = generate_gradient_image()
    cv2.imwrite(os.path.join(output_dir, 'gradient.jpg'), gradient)
    print("  ✓ 渐变图像")
    
    checkerboard = generate_checkerboard()
    cv2.imwrite(os.path.join(output_dir, 'checkerboard.jpg'), checkerboard)
    print("  ✓ 棋盘格图像")
    
    color_bars = generate_color_bars()
    cv2.imwrite(os.path.join(output_dir, 'color_bars.jpg'), color_bars)
    print("  ✓ 彩色条纹图像")
    
    shapes = generate_shapes()
    cv2.imwrite(os.path.join(output_dir, 'shapes.jpg'), shapes)
    print("  ✓ 几何形状图像")
    
    noise = generate_noise_image()
    cv2.imwrite(os.path.join(output_dir, 'noise.jpg'), noise)
    print("  ✓ 噪声图像")
    
    sample = generate_shapes(512, 512)
    cv2.imwrite('sample_input.jpg', sample)
    print("  ✓ 示例输入图像")
    
    print(f"\n测试图像已保存到：{output_dir}/")


if __name__ == '__main__':
    main()
