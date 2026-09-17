"""
XHS Text Overlay - 文字叠加节点
================================
在图片上叠加文字，用于小红书封面/图文标题制作。

功能:
    - 支持标题和正文
    - 可选字体、字号、颜色
    - 自定义位置
    - 自动换行
    - 批量处理
"""

from __future__ import annotations

import os

import torch

from ..lib.image_utils import draw_text

_CATEGORY = "XHS Tools"

# 默认字体搜索路径
_DEFAULT_FONT_CANDIDATES = [
    "C:/Windows/Fonts/msyh.ttc",          # 微软雅黑
    "C:/Windows/Fonts/simhei.ttf",         # 黑体
    "C:/Windows/Fonts/simsun.ttc",         # 宋体
    "/System/Library/Fonts/PingFang.ttc",  # macOS 苹方
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
]


def _find_default_font() -> str | None:
    """查找系统可用的中文字体。"""
    for path in _DEFAULT_FONT_CANDIDATES:
        if os.path.isfile(path):
            return path
    return None


class XHSTextOverlay:
    """在图片上叠加文字 - 适合小红书标题和正文。"""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "image": ("IMAGE", {
                    "tooltip": "底图",
                }),
                "text": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "要叠加的文字内容",
                }),
                "position_x": ("INT", {
                    "default": 60, "min": 0, "max": 8192, "step": 1,
                    "tooltip": "文字左上角 X 坐标",
                }),
                "position_y": ("INT", {
                    "default": 60, "min": 0, "max": 8192, "step": 1,
                    "tooltip": "文字左上角 Y 坐标",
                }),
                "font_size": ("INT", {
                    "default": 48, "min": 8, "max": 500, "step": 1,
                    "tooltip": "字号",
                }),
                "color_hex": ("STRING", {
                    "default": "#333333",
                    "tooltip": "文字颜色 HEX (如 #333333 深灰, #FF6B81 小红书红)",
                }),
                "max_width": ("INT", {
                    "default": 960, "min": 0, "max": 8192, "step": 1,
                    "tooltip": "最大宽度(px)，0=不限制，超出自动换行",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    FUNCTION = "add_text"
    CATEGORY = _CATEGORY
    DESCRIPTION = "在图片上叠加文字，支持中文和自动换行"

    def add_text(
        self,
        image: torch.Tensor,
        text: str,
        position_x: int,
        position_y: int,
        font_size: int,
        color_hex: str,
        max_width: int,
    ) -> tuple[torch.Tensor]:
        """绘制文字到图片上。"""
        if not text.strip():
            return (image,)

        color = self._parse_hex(color_hex)
        font_path = _find_default_font()

        results = []
        for i in range(image.shape[0]):
            img = image[i : i + 1]
            result = draw_text(
                img,
                text,
                (position_x, position_y),
                font_path=font_path,
                font_size=font_size,
                color=color,
                max_width=max_width if max_width > 0 else None,
            )
            results.append(result)

        return (torch.cat(results, dim=0),)

    @staticmethod
    def _parse_hex(hex_str: str) -> tuple[int, int, int]:
        """解析 HEX 颜色。"""
        hex_str = hex_str.lstrip("#")
        if len(hex_str) == 3:
            hex_str = "".join(c * 2 for c in hex_str)
        if len(hex_str) == 6:
            return (int(hex_str[0:2], 16), int(hex_str[2:4], 16), int(hex_str[4:6], 16))
        return (51, 51, 51)