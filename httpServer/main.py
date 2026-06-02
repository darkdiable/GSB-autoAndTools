#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简易HTTP服务器 - 启动入口
支持命令行参数自定义端口和静态目录
"""

import argparse
import sys
import os

# 添加src目录到Python路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from server import SimpleHttpServer


def parse_args():
    """解析命令行参数"""
    parser = argparse.ArgumentParser(
        description='简易HTTP服务器 - 静态文件服务',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python main.py                    # 使用默认配置（端口8000，static目录）
  python main.py -p 8080            # 指定端口8080
  python main.py -d /path/to/files  # 指定静态文件目录
  python main.py -H 127.0.0.1       # 仅允许本地访问
        """
    )
    
    parser.add_argument(
        '-p', '--port',
        type=int,
        default=8000,
        help='监听端口，默认: 8000'
    )
    
    parser.add_argument(
        '-H', '--host',
        type=str,
        default='0.0.0.0',
        help='监听地址，默认: 0.0.0.0（允许所有地址访问）'
    )
    
    parser.add_argument(
        '-d', '--dir',
        type=str,
        default=None,
        help='静态文件目录，默认: 当前目录下的static文件夹'
    )
    
    return parser.parse_args()


def main():
    """主函数"""
    args = parse_args()
    
    # 创建并启动服务器
    server = SimpleHttpServer(
        host=args.host,
        port=args.port,
        static_dir=args.dir
    )
    
    server.start()


if __name__ == '__main__':
    main()
