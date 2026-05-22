#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文件处理模块
提供文件和目录级别的简繁转换功能
"""

import os
import glob
from typing import List, Optional, Dict, Any
from pathlib import Path

from .converter import (
    ChineseConverter,
    ConversionDirection,
    SimplifiedToTraditionalConverter,
    TraditionalToSimplifiedConverter,
    ConversionError,
    InvalidInputError,
)


class FileConversionError(ConversionError):
    pass


class FileNotFoundError(FileConversionError):
    pass


class DirectoryNotFoundError(FileConversionError):
    pass


class FileEncodingError(FileConversionError):
    pass


class FilePermissionError(FileConversionError):
    pass


class FileConverter:
    def __init__(self, direction: ConversionDirection = ConversionDirection.SIMPLIFIED_TO_TRADITIONAL):
        self._converter = ChineseConverter(direction)
        self._default_encoding = 'utf-8'

    @property
    def direction(self) -> ConversionDirection:
        return self._converter.direction

    @direction.setter
    def direction(self, new_direction: ConversionDirection) -> None:
        self._converter.direction = new_direction

    @staticmethod
    def _validate_file_path(file_path: str) -> None:
        if not isinstance(file_path, str):
            raise InvalidInputError(
                f"文件路径必须是字符串类型，当前类型: {type(file_path).__name__}"
            )

        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"文件不存在: {file_path}")

        if not path.is_file():
            raise FileConversionError(f"路径不是文件: {file_path}")

    @staticmethod
    def _validate_directory_path(dir_path: str) -> None:
        if not isinstance(dir_path, str):
            raise InvalidInputError(
                f"目录路径必须是字符串类型，当前类型: {type(dir_path).__name__}"
            )

        path = Path(dir_path)
        if not path.exists():
            raise DirectoryNotFoundError(f"目录不存在: {dir_path}")

        if not path.is_dir():
            raise FileConversionError(f"路径不是目录: {dir_path}")

    def _read_file(self, file_path: str, encoding: Optional[str] = None) -> str:
        encoding = encoding or self._default_encoding
        try:
            with open(file_path, 'r', encoding=encoding) as f:
                return f.read()
        except UnicodeDecodeError as e:
            raise FileEncodingError(
                f"文件编码错误，使用 {encoding} 读取失败: {file_path}. 错误: {e}"
            ) from e
        except PermissionError as e:
            raise FilePermissionError(
                f"没有权限读取文件: {file_path}. 错误: {e}"
            ) from e
        except IOError as e:
            raise FileConversionError(
                f"读取文件失败: {file_path}. 错误: {e}"
            ) from e

    def _write_file(self, file_path: str, content: str, encoding: Optional[str] = None) -> None:
        encoding = encoding or self._default_encoding
        try:
            with open(file_path, 'w', encoding=encoding) as f:
                f.write(content)
        except PermissionError as e:
            raise FilePermissionError(
                f"没有权限写入文件: {file_path}. 错误: {e}"
            ) from e
        except IOError as e:
            raise FileConversionError(
                f"写入文件失败: {file_path}. 错误: {e}"
            ) from e

    def convert_file(
        self,
        input_path: str,
        output_path: Optional[str] = None,
        encoding: Optional[str] = None,
        in_place: bool = False,
    ) -> str:
        self._validate_file_path(input_path)

        content = self._read_file(input_path, encoding)
        converted_content = self._converter.convert(content)

        if in_place:
            output_path = input_path
        elif output_path is None:
            input_dir = os.path.dirname(input_path)
            input_name, input_ext = os.path.splitext(os.path.basename(input_path))
            suffix = '_t' if self.direction == ConversionDirection.SIMPLIFIED_TO_TRADITIONAL else '_s'
            output_path = os.path.join(input_dir, f"{input_name}{suffix}{input_ext}")

        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)

        self._write_file(output_path, converted_content, encoding)
        return output_path

    def convert_files(
        self,
        file_paths: List[str],
        output_dir: Optional[str] = None,
        encoding: Optional[str] = None,
        in_place: bool = False,
    ) -> Dict[str, Any]:
        if not isinstance(file_paths, list):
            raise InvalidInputError(
                f"文件路径列表必须是列表类型，当前类型: {type(file_paths).__name__}"
            )

        results = {
            'success': [],
            'failed': [],
            'total': len(file_paths),
        }

        for file_path in file_paths:
            try:
                if output_dir and not in_place:
                    file_name = os.path.basename(file_path)
                    input_name, input_ext = os.path.splitext(file_name)
                    suffix = '_t' if self.direction == ConversionDirection.SIMPLIFIED_TO_TRADITIONAL else '_s'
                    output_path = os.path.join(output_dir, f"{input_name}{suffix}{input_ext}")
                else:
                    output_path = None

                result_path = self.convert_file(
                    file_path,
                    output_path=output_path,
                    encoding=encoding,
                    in_place=in_place,
                )
                results['success'].append({
                    'input': file_path,
                    'output': result_path,
                    'status': 'success'
                })
            except FileConversionError as e:
                results['failed'].append({
                    'input': file_path,
                    'error': str(e),
                    'status': 'failed'
                })

        return results

    def convert_directory(
        self,
        input_dir: str,
        output_dir: Optional[str] = None,
        file_pattern: str = '*.txt',
        encoding: Optional[str] = None,
        recursive: bool = True,
    ) -> Dict[str, Any]:
        self._validate_directory_path(input_dir)

        if output_dir:
            os.makedirs(output_dir, exist_ok=True)

        pattern = os.path.join(input_dir, '**', file_pattern) if recursive else os.path.join(input_dir, file_pattern)
        file_paths = glob.glob(pattern, recursive=recursive)

        if not file_paths:
            return {
                'success': [],
                'failed': [],
                'total': 0,
                'message': f'在目录中未找到匹配 {file_pattern} 的文件'
            }

        return self.convert_files(
            file_paths,
            output_dir=output_dir,
            encoding=encoding,
            in_place=(output_dir is None),
        )


def convert_file(
    input_path: str,
    direction: str,
    output_path: Optional[str] = None,
    encoding: Optional[str] = None,
    in_place: bool = False,
) -> str:
    direction_map = {
        's2t': ConversionDirection.SIMPLIFIED_TO_TRADITIONAL,
        't2s': ConversionDirection.TRADITIONAL_TO_SIMPLIFIED,
    }

    if direction not in direction_map:
        raise InvalidInputError(
            f"无效的转换方向: {direction}. 支持的方向: {list(direction_map.keys())}"
        )

    file_converter = FileConverter(direction_map[direction])
    return file_converter.convert_file(
        input_path=input_path,
        output_path=output_path,
        encoding=encoding,
        in_place=in_place,
    )


def convert_directory(
    input_dir: str,
    direction: str,
    output_dir: Optional[str] = None,
    file_pattern: str = '*.txt',
    encoding: Optional[str] = None,
    recursive: bool = True,
) -> Dict[str, Any]:
    direction_map = {
        's2t': ConversionDirection.SIMPLIFIED_TO_TRADITIONAL,
        't2s': ConversionDirection.TRADITIONAL_TO_SIMPLIFIED,
    }

    if direction not in direction_map:
        raise InvalidInputError(
            f"无效的转换方向: {direction}. 支持的方向: {list(direction_map.keys())}"
        )

    file_converter = FileConverter(direction_map[direction])
    return file_converter.convert_directory(
        input_dir=input_dir,
        output_dir=output_dir,
        file_pattern=file_pattern,
        encoding=encoding,
        recursive=recursive,
    )
