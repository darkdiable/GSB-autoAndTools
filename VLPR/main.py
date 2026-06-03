import os
import sys
from pathlib import Path
from typing import List, Dict

sys.path.append(str(Path(__file__).parent))

from src.license_plate_recognizer import LicensePlateRecognizer
from src.char_filter import CharFilter


class VLPRRunner:
    def __init__(self, vlp_dir: str = "vlp"):
        self.vlp_dir = Path(vlp_dir)
        self.recognizer = LicensePlateRecognizer()
        self.char_filter = CharFilter()
        
        self.image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.webp'}

    def get_image_files(self) -> List[Path]:
        if not self.vlp_dir.exists():
            raise FileNotFoundError(f"目录不存在: {self.vlp_dir}")
        
        image_files = []
        for file_path in self.vlp_dir.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in self.image_extensions:
                image_files.append(file_path)
        
        return sorted(image_files)

    def process_images(self) -> Dict[str, str]:
        results = {}
        image_files = self.get_image_files()
        
        if not image_files:
            print(f"在 {self.vlp_dir} 目录下没有找到图片文件")
            return results
        
        for image_path in image_files:
            try:
                plate = self.recognizer.recognize_plate(str(image_path))
                results[image_path.name] = plate
            except Exception as e:
                print(f"处理图片 {image_path.name} 时出错: {str(e)}")
                results[image_path.name] = "无车牌信息"
        
        return results

    def print_results(self, results: Dict[str, str]) -> None:
        print("\n" + "="*50)
        print("车牌识别结果")
        print("="*50)
        for image_name, plate in results.items():
            print(f"{image_name} ： {plate}")
        print("="*50 + "\n")


def main():
    script_dir = Path(__file__).parent
    vlp_dir = script_dir / "vlp"
    
    try:
        runner = VLPRRunner(str(vlp_dir))
        results = runner.process_images()
        runner.print_results(results)
    except FileNotFoundError as e:
        print(f"错误: {str(e)}")
        print("请确保 vlp 目录存在并包含汽车照片")
        sys.exit(1)
    except Exception as e:
        print(f"发生错误: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
