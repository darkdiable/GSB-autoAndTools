#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简易HTTP服务器包
"""

from .server import SimpleHttpServer, StaticFileHandler

__all__ = ['SimpleHttpServer', 'StaticFileHandler']
__version__ = '1.0.0'
