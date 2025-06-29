"""
pixelart_mcp - 画像生成・ピクセルアート生成MCPサーバ

このパッケージは、MCPプロトコルを使用して画像生成とピクセルアート生成の
機能を提供するサーバーです。
"""

from .image_jobs import ImageJobManager

__version__ = "0.1.0"
__all__ = ["ImageJobManager"]
