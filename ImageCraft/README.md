# ImageCraft - 图像处理工具库

一个功能丰富的图像处理项目，支持多种图像滤镜、变换和分析功能。

## 项目结构

```
ImageCraft/
├── core/          # 核心处理模块
├── filters/       # 滤镜实现
├── utils/         # 工具函数
├── io/           # 输入输出处理
├── tests/        # 测试脚本
├── main.py       # 主程序入口
├── requirements.txt  # 依赖包
├── README.md     # 项目说明
└── BUG_GUIDE.md  # Bug 修复指南
```

## 安装

```bash
pip install -r requirements.txt
```

## 快速开始

### 1. 生成测试图像

```bash
cd ImageCraft
python tests/generate_test_images.py
```

### 2. 运行测试

```bash
python tests/test_suite.py
```

### 3. 运行主程序

```bash
python main.py
```

## 使用示例

```python
from core.processor import ImageProcessor
from filters import blur, edge_detection

processor = ImageProcessor()
processor.load_image('input.jpg')
processor.adjust_brightness(1.2)
processor.save('output.jpg')
```