"""
主程序入口 - 演示 ImageCraft 功能
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.processor import ImageProcessor
from core.pipeline import ProcessingPipeline
from filters import blur, edge_detection, enhance
from utils import image_utils, color_utils
from io.image_io import ImageLoader, ImageSaver


def main():
    """主函数"""
    print("=" * 60)
    print("ImageCraft - 图像处理工具")
    print("=" * 60)
    
    processor = ImageProcessor()
    
    try:
        input_image = 'sample_input.jpg'
        
        if os.path.exists(input_image):
            processor.load_image(input_image)
            print(f"✓ 已加载图像：{input_image}")
        else:
            print(f"⚠ 图像文件不存在：{input_image}")
            print("  使用测试图像继续...")
            
            import numpy as np
            test_img = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
            processor.image = test_img
            processor.original_image = test_img.copy()
            processor.metadata = {
                'width': 256,
                'height': 256,
                'channels': 3
            }
        
        print("\n执行图像处理流程...")
        
        processor.adjust_brightness(1.1)
        print("  ✓ 调整亮度")
        
        processor.adjust_contrast(1.2)
        print("  ✓ 调整对比度")
        
        current_img = processor.get_image()
        
        blurred = blur.gaussian_blur(current_img, sigma=2.0)
        print("  ✓ 应用高斯模糊")
        
        edges = edge_detection.canny_edge(current_img)
        print("  ✓ 应用 Canny 边缘检测")
        
        sharpened = enhance.sharpen(current_img, alpha=1.5)
        print("  ✓ 应用锐化")
        
        stats = processor.get_statistics()
        print(f"\n图像统计信息:")
        print(f"  均值：{stats['mean']:.2f}")
        print(f"  标准差：{stats['std']:.2f}")
        print(f"  最小值：{stats['min']:.2f}")
        print(f"  最大值：{stats['max']:.2f}")
        
        output_dir = 'output'
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        saver = ImageSaver()
        saver.save(current_img, os.path.join(output_dir, 'processed.jpg'))
        saver.save(blurred, os.path.join(output_dir, 'blurred.jpg'))
        saver.save(edges, os.path.join(output_dir, 'edges.jpg'))
        saver.save(sharpened, os.path.join(output_dir, 'sharpened.jpg'))
        
        print(f"\n✓ 已保存处理结果到：{output_dir}/")
        
        print("\n" + "=" * 60)
        print("处理完成!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ 错误：{e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
