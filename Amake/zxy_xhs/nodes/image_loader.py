"""
XHS Image Loader - 图片加载节点
================================
从本地文件系统或图片库加载图片，支持批量加载。

功能:
    - 从 ComfyUI input 目录选取图片
    - 支持批量加载多张图片
    - 可选缩放到目标尺寸

输出:
    - IMAGE: 图片 tensor (B,H,W,C)
    - MASK:  透明通道遮罩 (B,H,W) 或 None

性能优化:
    - 使用 TTL 缓存避免每次 INPUT_TYPES 调用都扫描目录
"""

from __future__ import annotations

import os
import time

import torch
import folder_paths
import node_helpers
from PIL import Image, ImageOps, ImageSequence
import numpy as np

from loguru import logger  

logger.remove()
_log_handler_id = logger.add(
    # sys.stderr,
    format=(
        # "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        # "<level>{level: <5}</level> | "
        # "<cyan>{extra[channel]}</cyan> | "
        # "<level>{message}</level>"
        "<green>{file}</green> : <cyan>{function}</cyan> : {line} | {message}"
    ),
    # level="INFO",
    colorize=True,
    filter=lambda record: record["extra"].setdefault("channel", "-") or True,
)


_CATEGORY = "XHS Tools"

_input_files_cache: tuple[float, list[str]] = (0.0, [])
_CACHE_TTL = 2.0


def _get_cached_input_files() -> list[str]:
    """获取 input 目录中的图片文件列表（带 TTL 缓存）。

    缓存 2 秒有效，避免 ComfyUI 频繁刷新节点定义时重复扫描目录。
    """
    global _input_files_cache
    now = time.monotonic()
    if now - _input_files_cache[0] < _CACHE_TTL:
        return _input_files_cache[1]

    input_dir = folder_paths.get_input_directory()
    files = []
    if os.path.isdir(input_dir):
        for f in os.listdir(input_dir):
            if os.path.isfile(os.path.join(input_dir, f)):
                files.append(f)
    files = sorted(folder_paths.filter_files_content_types(files, ["image"]))

    _input_files_cache = (now, files)
   
    return files


class XHSImageLoader:
    """小红书图片加载器 - 从文件或图库加载图片。"""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        files = _get_cached_input_files()
        return {
            "required": {
                "image": (files, {"image_upload": True}),
            },
            "optional": {
                "target_width": ("INT", {
                    "default": 0, "min": 0, "max": 8192, "step": 1,
                    "tooltip": "缩放目标宽度 (0=不缩放)",
                }),
                "target_height": ("INT", {
                    "default": 0, "min": 0, "max": 8192, "step": 1,
                    "tooltip": "缩放目标高度 (0=不缩放)",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE", "MASK")
    RETURN_NAMES = ("images", "mask")
    FUNCTION = "load_image"
    CATEGORY = _CATEGORY
    DESCRIPTION = "从 ComfyUI input 目录加载图片，支持缩放"

    def load_image(
        self,
        image: str,
        target_width: int = 0,
        target_height: int = 0,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """加载图片并返回 IMAGE 和 MASK。"""
        image_path = folder_paths.get_annotated_filepath(image)
        img = node_helpers.pillow(Image.open, image_path)
        logger.info("加载图片: {}", image_path)

        output_images = []
        output_masks = []

        for i in ImageSequence.Iterator(img):
            i = node_helpers.pillow(ImageOps.exif_transpose, i)
            if i.mode == "I":
                i = i.point(lambda x: x * 0.04).convert("L")
            image_only = i.convert("RGB")

            if target_width > 0 and target_height > 0:
                image_only = image_only.resize(
                    (target_width, target_height), Image.LANCZOS
                )

            if i.mode == "RGBA":
                mask = i.split()[-1]
            elif i.mode == "RGB":
                w, h = image_only.size
                mask = Image.new("L", (w, h), 255)
            else:
                mask = None

            output_images.append(image_only)
            if mask:
                output_masks.append(mask)

        if not output_images:
            raise RuntimeError(f"无法加载图片: {image_path}")

        images_tensor = []
        for img_pil in output_images:
            arr = np.array(img_pil).astype(np.float32) / 255.0
            images_tensor.append(torch.from_numpy(arr)[None,])

        image_out = torch.cat(images_tensor, dim=0)

        mask_out = torch.zeros(
            (image_out.shape[0], 64, 64), dtype=torch.float32
        )
        if output_masks:
            mask_tensors = []
            for m_pil in output_masks:
                m_arr = np.array(m_pil).astype(np.float32) / 255.0
                mask_tensors.append(torch.from_numpy(m_arr)[None,])
            mask_out = torch.cat(mask_tensors, dim=0)

        return (image_out, mask_out)