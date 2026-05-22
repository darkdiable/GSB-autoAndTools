#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
核心转换模块
提供简体中文与繁体中文的相互转换功能
"""

from enum import Enum
from typing import Optional, List

from .mapping import (
    SIMPLIFIED_TO_TRADITIONAL_BASIC,
    SIMPLIFIED_TO_TRADITIONAL_PHRASES,
    TRADITIONAL_TO_SIMPLIFIED_BASIC,
    TRADITIONAL_TO_SIMPLIFIED_PHRASES,
)


class ConversionDirection(Enum):
    SIMPLIFIED_TO_TRADITIONAL = 's2t'
    TRADITIONAL_TO_SIMPLIFIED = 't2s'


class ConversionError(Exception):
    pass


class InvalidInputError(ConversionError):
    pass


class UnsupportedDirectionError(ConversionError):
    pass


class ChineseConverter:
    def __init__(self, direction: ConversionDirection = ConversionDirection.SIMPLIFIED_TO_TRADITIONAL):
        if not isinstance(direction, ConversionDirection):
            raise UnsupportedDirectionError(
                f"无效的转换方向: {direction}. 请使用 ConversionDirection 枚举值"
            )
        self._direction = direction
        self._char_map, self._phrase_map = self._load_maps(direction)

    @staticmethod
    def _load_maps(direction: ConversionDirection) -> tuple:
        if direction == ConversionDirection.SIMPLIFIED_TO_TRADITIONAL:
            return SIMPLIFIED_TO_TRADITIONAL_BASIC, SIMPLIFIED_TO_TRADITIONAL_PHRASES
        else:
            return TRADITIONAL_TO_SIMPLIFIED_BASIC, TRADITIONAL_TO_SIMPLIFIED_PHRASES

    @property
    def direction(self) -> ConversionDirection:
        return self._direction

    @direction.setter
    def direction(self, new_direction: ConversionDirection) -> None:
        if not isinstance(new_direction, ConversionDirection):
            raise UnsupportedDirectionError(
                f"无效的转换方向: {new_direction}. 请使用 ConversionDirection 枚举值"
            )
        self._direction = new_direction
        self._char_map, self._phrase_map = self._load_maps(new_direction)

    def _convert_phrases(self, text: str) -> str:
        sorted_phrases = sorted(
            self._phrase_map.keys(),
            key=lambda x: len(x),
            reverse=True
        )
        for phrase in sorted_phrases:
            if phrase in text:
                text = text.replace(phrase, self._phrase_map[phrase])
        return text

    def _convert_chars(self, text: str) -> str:
        result = []
        for char in text:
            result.append(self._char_map.get(char, char))
        return ''.join(result)

    def convert(self, text: str) -> str:
        if not isinstance(text, str):
            raise InvalidInputError(
                f"输入必须是字符串类型，当前类型: {type(text).__name__}"
            )

        if not text:
            return text

        text = self._convert_phrases(text)
        text = self._convert_chars(text)
        return text

    def convert_batch(self, texts: List[str]) -> List[str]:
        if not isinstance(texts, list):
            raise InvalidInputError(
                f"输入必须是列表类型，当前类型: {type(texts).__name__}"
            )
        return [self.convert(text) for text in texts]


class SimplifiedToTraditionalConverter(ChineseConverter):
    def __init__(self):
        super().__init__(ConversionDirection.SIMPLIFIED_TO_TRADITIONAL)


class TraditionalToSimplifiedConverter(ChineseConverter):
    def __init__(self):
        super().__init__(ConversionDirection.TRADITIONAL_TO_SIMPLIFIED)


def convert(text: str, direction: str) -> str:
    direction_map = {
        's2t': ConversionDirection.SIMPLIFIED_TO_TRADITIONAL,
        't2s': ConversionDirection.TRADITIONAL_TO_SIMPLIFIED,
        'simplified_to_traditional': ConversionDirection.SIMPLIFIED_TO_TRADITIONAL,
        'traditional_to_simplified': ConversionDirection.TRADITIONAL_TO_SIMPLIFIED,
    }

    if direction not in direction_map:
        raise UnsupportedDirectionError(
            f"无效的转换方向: {direction}. "
            f"支持的方向: {list(direction_map.keys())}"
        )

    converter = ChineseConverter(direction_map[direction])
    return converter.convert(text)


def simplified_to_traditional(text: str) -> str:
    converter = SimplifiedToTraditionalConverter()
    return converter.convert(text)


def traditional_to_simplified(text: str) -> str:
    converter = TraditionalToSimplifiedConverter()
    return converter.convert(text)
