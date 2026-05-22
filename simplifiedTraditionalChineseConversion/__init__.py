#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中文简繁转换工具包
================

功能：
- 简体中文 <-> 繁体中文 双向转换
- 单字符串转换
- 批量文件转换（UTF-8 文本）

使用示例：
    from simplifiedTraditionalChineseConversion import (
        simplified_to_traditional,
        traditional_to_simplified,
        convert_file,
        convert_directory,
        ChineseConverter,
        FileConverter,
        ConversionDirection,
    )

    # 简繁字符串转换
    traditional_text = simplified_to_traditional('中国文化')
    simplified_text = traditional_to_simplified('中國文化')

    # 文件转换
    convert_file('input.txt', 's2t', output_path='output.txt')

    # 批量目录转换
    convert_directory('input_dir/', 't2s', output_dir='output_dir/')
"""

__version__ = '1.0.0'
__author__ = 'Chinese Converter Team'

from .converter import (
    ConversionDirection,
    ConversionError,
    InvalidInputError,
    UnsupportedDirectionError,
    ChineseConverter,
    SimplifiedToTraditionalConverter,
    TraditionalToSimplifiedConverter,
    convert,
    simplified_to_traditional,
    traditional_to_simplified,
)

from .file_handler import (
    FileConversionError,
    FileNotFoundError,
    DirectoryNotFoundError,
    FileEncodingError,
    FilePermissionError,
    FileConverter,
    convert_file,
    convert_directory,
)

from .mapping import (
    SIMPLIFIED_TO_TRADITIONAL_BASIC,
    TRADITIONAL_TO_SIMPLIFIED_BASIC,
    SIMPLIFIED_TO_TRADITIONAL_PHRASES,
    TRADITIONAL_TO_SIMPLIFIED_PHRASES,
)

__all__ = [
    'ConversionDirection',
    'ConversionError',
    'InvalidInputError',
    'UnsupportedDirectionError',
    'ChineseConverter',
    'SimplifiedToTraditionalConverter',
    'TraditionalToSimplifiedConverter',
    'convert',
    'simplified_to_traditional',
    'traditional_to_simplified',
    'FileConversionError',
    'FileNotFoundError',
    'DirectoryNotFoundError',
    'FileEncodingError',
    'FilePermissionError',
    'FileConverter',
    'convert_file',
    'convert_directory',
    'SIMPLIFIED_TO_TRADITIONAL_BASIC',
    'TRADITIONAL_TO_SIMPLIFIED_BASIC',
    'SIMPLIFIED_TO_TRADITIONAL_PHRASES',
    'TRADITIONAL_TO_SIMPLIFIED_PHRASES',
]
