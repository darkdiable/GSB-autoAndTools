#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
中文简繁转换工具 - 使用示例
==========================

本文件展示了如何使用 simplifiedTraditionalChineseConversion 包的各种功能。
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simplifiedTraditionalChineseConversion import (
    simplified_to_traditional,
    traditional_to_simplified,
    convert,
    convert_file,
    convert_directory,
    ChineseConverter,
    FileConverter,
    ConversionDirection,
    ConversionError,
    InvalidInputError,
    UnsupportedDirectionError,
    FileNotFoundError,
)


def example_1_basic_conversion():
    print("=" * 60)
    print("示例 1: 基础字符串转换")
    print("=" * 60)

    simplified_text = "我们热爱中国文化，学习计算机技术。"
    print(f"\n简体原文: {simplified_text}")

    traditional_text = simplified_to_traditional(simplified_text)
    print(f"转换为繁体: {traditional_text}")

    converted_back = traditional_to_simplified(traditional_text)
    print(f"转回简体:   {converted_back}")


def example_2_phrase_conversion():
    print("\n" + "=" * 60)
    print("示例 2: 词汇优先转换")
    print("=" * 60)

    text = "为什么这样做？因为我们认识到这是正确的选择。"
    print(f"\n简体原文: {text}")

    result = simplified_to_traditional(text)
    print(f"转换结果: {result}")
    print("说明: '为什么' -> '為什麼', '这样' -> '這樣', '认识' -> '認識'")


def example_3_convert_function():
    print("\n" + "=" * 60)
    print("示例 3: 使用通用 convert 函数")
    print("=" * 60)

    text = "互联网软件和硬件开发。"
    print(f"\n原文: {text}")

    result_s2t = convert(text, 's2t')
    print(f"s2t:  {result_s2t}")

    result_t2s = convert(result_s2t, 't2s')
    print(f"t2s:  {result_t2s}")

    try:
        convert(text, 'invalid')
    except UnsupportedDirectionError as e:
        print(f"\n错误处理演示: {e}")


def example_4_chinese_converter_class():
    print("\n" + "=" * 60)
    print("示例 4: 使用 ChineseConverter 类")
    print("=" * 60)

    converter = ChineseConverter(ConversionDirection.SIMPLIFIED_TO_TRADITIONAL)
    print(f"\n当前转换方向: {converter.direction}")

    texts = [
        "这是第一个测试句子。",
        "这是第二个测试句子，包含更多内容。",
        "学习历史和地理是很重要的。"
    ]

    print("\n批量转换:")
    results = converter.convert_batch(texts)
    for original, converted in zip(texts, results):
        print(f"  简: {original}")
        print(f"  繁: {converted}")
        print()

    converter.direction = ConversionDirection.TRADITIONAL_TO_SIMPLIFIED
    print(f"切换转换方向: {converter.direction}")
    print(f"转回: {converter.convert(results[0])}")


def example_5_specialized_converters():
    print("\n" + "=" * 60)
    print("示例 5: 使用专用转换器类")
    print("=" * 60)

    s2t_converter = ChineseConverter(ConversionDirection.SIMPLIFIED_TO_TRADITIONAL)
    t2s_converter = ChineseConverter(ConversionDirection.TRADITIONAL_TO_SIMPLIFIED)

    text = "北京和上海是中国的两个重要城市。"
    print(f"\n简体: {text}")

    traditional = s2t_converter.convert(text)
    print(f"繁体: {traditional}")

    simplified = t2s_converter.convert(traditional)
    print(f"简体: {simplified}")


def example_6_error_handling():
    print("\n" + "=" * 60)
    print("示例 6: 错误处理")
    print("=" * 60)

    try:
        simplified_to_traditional(123)
    except InvalidInputError as e:
        print(f"\n输入类型错误: {e}")

    try:
        convert_file('nonexistent_file.txt', 's2t')
    except FileNotFoundError as e:
        print(f"文件不存在错误: {e}")

    try:
        ChineseConverter('invalid_direction')
    except UnsupportedDirectionError as e:
        print(f"方向参数错误: {e}")


def example_7_file_conversion():
    print("\n" + "=" * 60)
    print("示例 7: 文件转换")
    print("=" * 60)

    test_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    os.makedirs(test_dir, exist_ok=True)

    input_file = os.path.join(test_dir, 'sample_simplified.txt')
    with open(input_file, 'w', encoding='utf-8') as f:
        f.write("这是一个测试文件。\n")
        f.write("我们在学习中文简繁转换技术。\n")
        f.write("第一行：计算机软件和硬件\n")
        f.write("第二行：互联网与数据科学\n")
        f.write("第三行：人工智能和机器学习\n")

    print(f"\n创建测试文件: {input_file}")
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    print(f"文件内容:\n{content}")

    output_file = os.path.join(test_dir, 'sample_traditional.txt')
    result_path = convert_file(input_file, 's2t', output_path=output_file)
    print(f"转换后的文件: {result_path}")

    with open(result_path, 'r', encoding='utf-8') as f:
        converted_content = f.read()
    print(f"转换后内容:\n{converted_content}")

    converted_back_file = os.path.join(test_dir, 'sample_back_to_simplified.txt')
    convert_file(result_path, 't2s', output_path=converted_back_file)
    print(f"转回简体文件: {converted_back_file}")

    with open(converted_back_file, 'r', encoding='utf-8') as f:
        back_content = f.read()
    print(f"转回后内容:\n{back_content}")

    assert content == back_content, "转换不一致！"
    print("✓ 双向转换验证通过！")


def example_8_batch_directory_conversion():
    print("\n" + "=" * 60)
    print("示例 8: 批量目录转换")
    print("=" * 60)

    test_dir = os.path.join(os.path.dirname(__file__), 'test_data', 'batch_input')
    output_dir = os.path.join(os.path.dirname(__file__), 'test_data', 'batch_output')
    os.makedirs(test_dir, exist_ok=True)
    os.makedirs(output_dir, exist_ok=True)

    for i in range(1, 4):
        file_path = os.path.join(test_dir, f'document_{i}.txt')
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(f"这是第 {i} 个文档。\n")
            f.write(f"文档内容：中国的历史和文化源远流长。\n")
            f.write(f"我们热爱学习科学技术知识。")

    print(f"\n创建了 3 个测试文件在: {test_dir}")

    results = convert_directory(
        test_dir,
        's2t',
        output_dir=output_dir,
        file_pattern='*.txt',
        recursive=False
    )

    print(f"\n转换结果:")
    print(f"  总文件数: {results['total']}")
    print(f"  成功: {len(results['success'])}")
    print(f"  失败: {len(results['failed'])}")

    for success in results['success']:
        print(f"  ✓ {success['input']} -> {success['output']}")

    output_files = os.listdir(output_dir)
    print(f"\n输出目录文件: {output_files}")

    if output_files:
        sample_output = os.path.join(output_dir, output_files[0])
        with open(sample_output, 'r', encoding='utf-8') as f:
            print(f"\n示例输出内容:\n{f.read()}")


def example_9_file_converter_class():
    print("\n" + "=" * 60)
    print("示例 9: 使用 FileConverter 类")
    print("=" * 60)

    test_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    input_file = os.path.join(test_dir, 'input.txt')

    file_converter = FileConverter(ConversionDirection.SIMPLIFIED_TO_TRADITIONAL)
    print(f"\nFileConverter 当前方向: {file_converter.direction}")

    output1 = file_converter.convert_file(
        input_file,
        output_path=os.path.join(test_dir, 'using_class_t.txt')
    )
    print(f"转换输出: {output1}")

    file_converter.direction = ConversionDirection.TRADITIONAL_TO_SIMPLIFIED
    print(f"切换方向后: {file_converter.direction}")

    output2 = file_converter.convert_file(
        output1,
        output_path=os.path.join(test_dir, 'using_class_s.txt')
    )
    print(f"转回输出: {output2}")

    with open(input_file, 'r', encoding='utf-8') as f:
        original = f.read()
    with open(output2, 'r', encoding='utf-8') as f:
        converted_back = f.read()

    assert original == converted_back, "转换不一致！"
    print("✓ FileConverter 双向转换验证通过！")


def example_10_in_place_conversion():
    print("\n" + "=" * 60)
    print("示例 10: 原地文件转换")
    print("=" * 60)

    test_dir = os.path.join(os.path.dirname(__file__), 'test_data')
    in_place_file = os.path.join(test_dir, 'in_place_test.txt')

    with open(in_place_file, 'w', encoding='utf-8') as f:
        f.write("这是一个用于测试原地转换的文件。\n")
        f.write("内容将被直接修改。")

    print(f"\n原始文件内容:")
    with open(in_place_file, 'r', encoding='utf-8') as f:
        print(f.read())

    print("\n执行原地转换 (s2t)...")
    result = convert_file(in_place_file, 's2t', in_place=True)
    print(f"转换后文件路径（不变）: {result}")

    print(f"\n转换后文件内容:")
    with open(in_place_file, 'r', encoding='utf-8') as f:
        print(f.read())

    print("\n执行原地转换 (t2s)...")
    convert_file(in_place_file, 't2s', in_place=True)
    print(f"\n转回后文件内容:")
    with open(in_place_file, 'r', encoding='utf-8') as f:
        print(f.read())


def main():
    print("\n" + "#" * 60)
    print("#            中文简繁转换工具 - 使用示例演示              #")
    print("#" * 60)

    examples = [
        example_1_basic_conversion,
        example_2_phrase_conversion,
        example_3_convert_function,
        example_4_chinese_converter_class,
        example_5_specialized_converters,
        example_6_error_handling,
        example_7_file_conversion,
        example_8_batch_directory_conversion,
        example_9_file_converter_class,
        example_10_in_place_conversion,
    ]

    success_count = 0
    for example in examples:
        try:
            example()
            success_count += 1
        except Exception as e:
            print(f"\n✗ 示例 {example.__name__} 执行失败: {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"示例执行完成: {success_count}/{len(examples)} 个示例成功")
    print("=" * 60)

    if success_count == len(examples):
        print("\n🎉 所有示例执行成功！")
    else:
        print(f"\n⚠️  有 {len(examples) - success_count} 个示例失败")

    print("\n提示: 查看 test_data 目录查看生成的测试文件")
    print("\n常用快速调用:")
    print("  simplified_to_traditional('文本')  # 简转繁")
    print("  traditional_to_simplified('文本')  # 繁转简")
    print("  convert_file('input.txt', 's2t')   # 文件简转繁")
    print("  convert_directory('dir/', 't2s')   # 目录繁转简")


if __name__ == '__main__':
    main()
