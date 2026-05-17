import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from epub_parser import EpubParser


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    epub_dir = os.path.join(script_dir, 'epub')
    output_dir = os.path.join(script_dir, 'output')

    if not os.path.exists(epub_dir):
        print(f"错误: epub目录不存在: {epub_dir}")
        return

    epub_files = list(Path(epub_dir).glob('*.epub'))
    if not epub_files:
        print(f"错误: 在 {epub_dir} 中未找到epub文件")
        return

    os.makedirs(output_dir, exist_ok=True)

    for epub_file in epub_files:
        print(f"\n开始解析: {epub_file.name}")
        try:
            parser = EpubParser(str(epub_file), output_dir)
            parser.parse()
        except Exception as e:
            print(f"解析 {epub_file.name} 时出错: {e}")
            import traceback
            traceback.print_exc()

    print(f"\n所有文件解析完成！输出目录: {output_dir}")


if __name__ == '__main__':
    main()
