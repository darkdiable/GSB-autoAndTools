import re
from typing import List


class CharFilter:
    def __init__(self):
        self.valid_pattern = re.compile(r'[^\u4e00-\u9fa5A-Za-z0-9]')
        
        self.provinces = {
            '京', '津', '冀', '晋', '蒙', '辽', '吉', '黑',
            '沪', '苏', '浙', '皖', '闽', '赣', '鲁', '豫',
            '鄂', '湘', '粤', '桂', '琼', '渝', '川', '贵',
            '云', '藏', '陕', '甘', '青', '宁', '新'
        }
        
        self.valid_letters = set('ABCDEFGHJKLMNPQRSTUVWXYZ')
        self.valid_digits = set('0123456789')

    def clean_text(self, text: str) -> str:
        cleaned = self.valid_pattern.sub('', text)
        cleaned = cleaned.upper()
        return cleaned

    def validate_plate_format(self, plate: str) -> bool:
        if len(plate) < 7 or len(plate) > 8:
            return False
        
        if plate[0] not in self.provinces:
            return False
        
        if plate[1] not in self.valid_letters:
            return False
        
        for char in plate[2:]:
            if char not in self.valid_letters and char not in self.valid_digits:
                return False
        
        return True

    def filter_plates(self, plates: List[str]) -> List[str]:
        valid_plates = []
        for plate in plates:
            cleaned = self.clean_text(plate)
            if cleaned and self.validate_plate_format(cleaned):
                valid_plates.append(cleaned)
        return valid_plates

    def extract_best_plate(self, plates: List[str]) -> str:
        valid_plates = self.filter_plates(plates)
        
        if not valid_plates:
            return "无车牌信息"
        
        valid_plates.sort(key=lambda x: len(x), reverse=True)
        
        return valid_plates[0]
