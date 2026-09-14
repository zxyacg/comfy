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
"""

from __future__ import annotations

import os

import torch
import folder_paths
import node_helpers
from PIL import Image, ImageOps, ImageSequence
import numpy as np


_CATEGORY = "XHS Tools"


class XHSImageLoader:
    """小红书图片加载器 - 从文件或图库加载图片。"""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        input_dir = folder_paths.get_input_directory()
        files = []
        if os.path.isdir(input_dir):
            for f in os.listdir(input_dir):
                if os.path.isfile(os.path.join(input_dir, f)):
                    files.append(f)
        files = folder_paths.filter_files_content_types(files, ["image"])
        return {
            "required": {
                "image": (sorted(files), {"image_upload": True}),
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

        output_images = []
        output_masks = []

        for i in ImageSequence.Iterator(img):
            i = node_helpers.pillow(ImageOps.exif_transpose, i)
            if i.mode == "I":
                i = i.point(lambda x: x * 0.04).convert("L")
            image_only = i.convert("RGB")

            # 缩放逻辑
            if target_width > 0 and target_height > 0:
                image_only = image_only.resize((target_width, target_height), Image.LANCZOS)

            # 构建 alpha 遮罩
            if i.mode == "RGBA":
                mask = i.split()[-1]
            elif i.mode == "RGB":
                # 为没有透明通道的图片创建全白遮罩
                w, h = image_only.size
                mask = Image.new("L", (w, h), 255)
            else:
                mask = None

            output_images.append(image_only)
            if mask:
                output_masks.append(mask)

        if not output_images:
            raise RuntimeError(f"无法加载图片: {image_path}")

        # 转换为 tensor
        images_tensor = []
        for img_pil in output_images:
            arr = np.array(img_pil).astype(np.float32) / 255.0
            images_tensor.append(torch.from_numpy(arr)[None,])

        image_out = torch.cat(images_tensor, dim=0)

        mask_out = torch.zeros((image_out.shape[0], 64, 64), dtype=torch.float32)
        if output_masks:
            mask_tensors = []
            for m_pil in output_masks:
                m_arr = np.array(m_pil).astype(np.float32) / 255.0
                mask_tensors.append(torch.from_numpy(m_arr)[None,])
            mask_out = torch.cat(mask_tensors, dim=0)

        return (image_out, mask_out)


class XHSImageLoaderSimple:
    """简化版图片加载 - 加载单张图片，无缩放选项。"""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        input_dir = folder_paths.get_input_directory()
        files = []
        if os.path.isdir(input_dir):
            for f in os.listdir(input_dir):
                if os.path.isfile(os.path.join(input_dir, f)):
                    files.append(f)
        files = folder_paths.filter_files_content_types(files, ["image"])
        return {
            "required": {
                "image": (sorted(files), {"image_upload": True}),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    FUNCTION = "load_image"
    CATEGORY = _CATEGORY

    def load_image(self, image: str) -> tuple[torch.Tensor]:
        image_path = folder_paths.get_annotated_filepath(image)
        img = node_helpers.pillow(Image.open, image_path)
        img = node_helpers.pillow(ImageOps.exif_transpose, img)
        img = img.convert("RGB")
        arr = np.array(img).astype(np.float32) / 255.0
        return (torch.from_numpy(arr)[None,],)