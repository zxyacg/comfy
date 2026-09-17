"""
XHS Canvas - 画布节点
======================
创建自定义尺寸和分辨率的空白画布。

支持:
    - 自定义宽度和高度
    - 批量创建多张画布
    - 画布背景颜色
    - 预设小红书尺寸 (3:4, 1:1, 9:16)
"""

from __future__ import annotations

import torch
from ..lib.image_utils import create_blank_canvas

_CATEGORY = "XHS Tools"

# 小红书常用尺寸预设 (宽 x 高)
XHS_PRESETS = {
    "竖版 3:4 (1080x1440)": (1080, 1440),
    "竖版 3:4 (1242x1660)": (1242, 1660),
    "方形 1:1 (1080x1080)": (1080, 1080),
    "横版 4:3 (1440x1080)": (1440, 1080),
    "横版 16:9 (1920x1080)": (1920, 1080),
    "自定义": (0, 0),
}


class XHSCanvas:
    """创建小红书适配的空白画布。"""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "preset": (list(XHS_PRESETS.keys()), {
                    "default": "竖版 3:4 (1080x1440)",
                    "tooltip": "小红书常用尺寸预设",
                }),
                "width": ("INT", {
                    "default": 1080, "min": 64, "max": 8192, "step": 1,
                    "tooltip": "画布宽度（预设选择'自定义'时生效）",
                }),
                "height": ("INT", {
                    "default": 1440, "min": 64, "max": 8192, "step": 1,
                    "tooltip": "画布高度（预设选择'自定义'时生效）",
                }),
                "background_color": ("STRING", {
                    "default": "#FFFFFF",
                    "tooltip": "背景色 HEX (如 #FFFFFF 白色, #F5F5F5 浅灰)",
                }),
                "batch_size": ("INT", {
                    "default": 1, "min": 1, "max": 64, "step": 1,
                    "tooltip": "批量生成的画布数量",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("canvas",)
    FUNCTION = "create_canvas"
    CATEGORY = _CATEGORY
    DESCRIPTION = "创建小红书适配的空白画布，支持预设和自定义尺寸"

    def create_canvas(
        self,
        preset: str,
        width: int,
        height: int,
        background_color: str,
        batch_size: int,
    ) -> tuple[torch.Tensor]:
        """创建画布。"""
        # 解析尺寸
        if preset != "自定义":
            width, height = XHS_PRESETS[preset]

        # 解析颜色
        color = self._parse_hex_color(background_color)

        # 批量创建
        canvases = []
        for _ in range(batch_size):
            canvas = create_blank_canvas(width, height, color)
            canvases.append(canvas)

        return (torch.cat(canvases, dim=0),)

    @staticmethod
    def _parse_hex_color(hex_str: str) -> tuple[int, int, int]:
        """解析 HEX 颜色值 (#RRGGBB) 为 RGB 元组。"""
        hex_str = hex_str.lstrip("#")
        if len(hex_str) == 3:
            hex_str = "".join(c * 2 for c in hex_str)
        if len(hex_str) == 6:
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            return (r, g, b)
        return (255, 255, 255)  # 默认白色