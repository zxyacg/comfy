"""
XHS Export - 导出节点
======================
将生成的图片批量导出，适配小红书发布格式。

功能:
    - 批量导出图片
    - 自定义文件名前缀
    - 选择保存目录 (output/temp)
    - PNG/JPEG 格式支持
    - 可调节 JPEG 压缩质量

输出:
    - 保存图片到磁盘
    - 返回 IMAGE 用于后续处理
"""

from __future__ import annotations

import json
import os
import numpy as np
from PIL import Image, PngImagePlugin

import folder_paths
import torch

_CATEGORY = "XHS Tools"


class XHSExport:
    """小红书图片导出 - 批量保存并返回图片。"""

    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "images": ("IMAGE", {
                    "tooltip": "要导出的图片",
                }),
                "filename_prefix": ("STRING", {
                    "default": "XHS_",
                    "tooltip": "文件名前缀",
                }),
                "format": (["png", "jpeg"], {
                    "default": "png",
                    "tooltip": "保存格式",
                }),
                "quality": ("INT", {
                    "default": 95, "min": 10, "max": 100, "step": 1,
                    "tooltip": "JPEG 质量 (仅 JPEG 格式生效)",
                }),
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO",
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("images",)
    OUTPUT_NODE = True
    FUNCTION = "export_images"
    CATEGORY = _CATEGORY
    DESCRIPTION = "批量导出图片到 ComfyUI output 目录，适配小红书发布"

    def export_images(
        self,
        images: torch.Tensor,
        filename_prefix: str = "XHS_",
        format: str = "png",
        quality: int = 95,
        prompt: dict | None = None,
        extra_pnginfo: dict | None = None,
    ) -> tuple[torch.Tensor]:
        """导出图片到磁盘。"""
        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = (
            folder_paths.get_save_image_path(
                filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0]
            )
        )

        results = []
        for batch_number, image in enumerate(images):
            # Tensor -> PIL
            i = 255.0 * image.cpu().numpy()
            img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))

            # 元数据
            metadata = None
            if format == "png":
                metadata = PngImagePlugin.PngInfo()
                if prompt is not None:
                    metadata.add_text("prompt", json.dumps(prompt))
                if extra_pnginfo is not None:
                    for k, v in extra_pnginfo.items():
                        metadata.add_text(k, json.dumps(v))

            # 保存
            filename_with_batch = filename.replace("%batch_num%", str(batch_number))
            ext = "jpg" if format == "jpeg" else "png"
            file = f"{filename_with_batch}_{counter:05}.{ext}"

            save_path = os.path.join(full_output_folder, file)
            if format == "jpeg":
                img.save(save_path, format="JPEG", quality=quality)
            else:
                img.save(save_path, pnginfo=metadata, compress_level=self.compress_level)

            results.append({
                "filename": file,
                "subfolder": subfolder,
                "type": self.type,
            })
            counter += 1

        return {"ui": {"images": results}, "result": (images,)}