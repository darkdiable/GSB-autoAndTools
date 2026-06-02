#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简易HTTP服务器模块 - 支持静态文件服务
"""

import os
import mimetypes
from http.server import HTTPServer, SimpleHTTPRequestHandler
from typing import Optional


class StaticFileHandler(SimpleHTTPRequestHandler):
    """自定义静态文件请求处理器"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=kwargs.pop('directory', '.'), **kwargs)
    
    def log_message(self, format: str, *args) -> None:
        """自定义日志输出格式"""
        client_ip = self.client_address[0]
        method = self.command
        path = self.path
        status = args[1] if len(args) > 1 else '-'
        print(f"[{client_ip}] {method} {path} - {status}")
    
    def do_GET(self) -> None:
        """处理GET请求"""
        super().do_GET()
    
    def guess_type(self, path: str) -> str:
        """猜测文件MIME类型"""
        mimetype, _ = mimetypes.guess_type(path)
        return mimetype or 'application/octet-stream'


class SimpleHttpServer:
    """简易HTTP服务器类"""
    
    def __init__(self, host: str = '0.0.0.0', port: int = 8000, 
                 static_dir: Optional[str] = None):
        """
        初始化服务器
        
        Args:
            host: 监听地址，默认0.0.0.0（允许外部访问）
            port: 监听端口，默认8000
            static_dir: 静态文件目录，默认当前目录下的static文件夹
        """
        self.host = host
        self.port = port
        
        # 设置静态文件目录
        if static_dir is None:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.static_dir = os.path.join(base_dir, 'static')
        else:
            self.static_dir = os.path.abspath(static_dir)
        
        # 确保静态目录存在
        os.makedirs(self.static_dir, exist_ok=True)
        
        self.server: Optional[HTTPServer] = None
    
    def start(self) -> None:
        """启动服务器"""
        # 创建自定义处理器，绑定静态目录
        def handler_factory(*args, **kwargs):
            return StaticFileHandler(*args, directory=self.static_dir, **kwargs)
        
        # 创建HTTP服务器实例
        self.server = HTTPServer((self.host, self.port), handler_factory)
        
        print(f"\n{'='*50}")
        print(f"简易HTTP服务器已启动")
        print(f"{'='*50}")
        print(f"监听地址: http://{self.host}:{self.port}")
        print(f"本地访问: http://localhost:{self.port}")
        print(f"静态目录: {self.static_dir}")
        print(f"{'='*50}")
        print("按 Ctrl+C 停止服务器\n")
        
        try:
            self.server.serve_forever()
        except KeyboardInterrupt:
            print("\n\n服务器已停止")
        finally:
            self.stop()
    
    def stop(self) -> None:
        """停止服务器"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            self.server = None
