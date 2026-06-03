import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple, Optional
import re


class LicensePlateRecognizer:
    def __init__(self):
        self.valid_chars_pattern = re.compile(r'[^\u4e00-\u9fa5A-Za-z0-9]')
        
        self.provinces = [
            '京', '津', '冀', '晋', '蒙', '辽', '吉', '黑',
            '沪', '苏', '浙', '皖', '闽', '赣', '鲁', '豫',
            '鄂', '湘', '粤', '桂', '琼', '渝', '川', '贵',
            '云', '藏', '陕', '甘', '青', '宁', '新'
        ]
        
        self.color_ranges = {
            'blue': ([100, 80, 80], [130, 255, 255]),
            'green': ([35, 40, 40], [85, 255, 255]),
            'yellow': ([20, 100, 100], [40, 255, 255])
        }
        
        self.hyperlpr_model = None
        self._init_hyperlpr()

    def _init_hyperlpr(self) -> None:
        try:
            from hyperlpr3 import LicensePlateCatcher
            self.hyperlpr_model = LicensePlateCatcher()
        except ImportError:
            self.hyperlpr_model = None

    def filter_invalid_chars(self, plate_text: str) -> str:
        cleaned = self.valid_chars_pattern.sub('', plate_text)
        cleaned = cleaned.upper()
        return cleaned

    def is_valid_plate(self, plate_text: str) -> bool:
        if len(plate_text) < 7 or len(plate_text) > 8:
            return False
        
        if plate_text[0] not in self.provinces:
            return False
        
        if not plate_text[1].isalpha():
            return False
        
        for char in plate_text[2:]:
            if not char.isalnum():
                return False
        
        return True

    def recognize_with_hyperlpr(self, image_path: str) -> str:
        if self.hyperlpr_model is None:
            return None
        
        try:
            import cv2
            image = cv2.imread(image_path)
            if image is None:
                return None
            
            results = self.hyperlpr_model(image)
            
            if not results:
                return None
            
            best_result = max(results, key=lambda x: x[1])
            plate_text = best_result[0]
            
            cleaned_plate = self.filter_invalid_chars(plate_text)
            
            if len(cleaned_plate) >= 7:
                return cleaned_plate
            
            return None
        except Exception as e:
            print(f"HyperLPR识别出错: {str(e)}")
            return None

    def detect_plate_by_color(self, image: np.ndarray) -> Optional[Tuple[np.ndarray, str]]:
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        for color_name, (lower, upper) in self.color_ranges.items():
            lower_np = np.array(lower, dtype=np.uint8)
            upper_np = np.array(upper, dtype=np.uint8)
            
            mask = cv2.inRange(hsv, lower_np, upper_np)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
            mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
            mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
            
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / float(h)
                
                if 2.0 < aspect_ratio < 6.0 and w > 60 and h > 20:
                    plate_region = image[y:y+h, x:x+w]
                    return plate_region, color_name
        
        return None

    def recognize_plate_opencv(self, image_path: str) -> str:
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"无法读取图片: {image_path}")
            
            plate_result = self.detect_plate_by_color(image)
            
            if plate_result:
                plate_region, color = plate_result
                return f"检测到{color}色车牌区域"
            
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            edges = cv2.Canny(gray, 100, 200)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
            edges = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
            
            contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                aspect_ratio = w / float(h)
                
                if 2.0 < aspect_ratio < 6.0 and w > 60 and h > 20:
                    return "检测到车牌区域"
            
            return "无车牌信息"
            
        except Exception as e:
            print(f"OpenCV识别过程中发生错误: {str(e)}")
            return "无车牌信息"

    def recognize_plate(self, image_path: str) -> str:
        try:
            if self.hyperlpr_model is not None:
                hyperlpr_result = self.recognize_with_hyperlpr(image_path)
                if hyperlpr_result:
                    return hyperlpr_result
            
            return self.recognize_plate_opencv(image_path)
            
        except Exception as e:
            print(f"识别过程中发生错误: {str(e)}")
            return "无车牌信息"
