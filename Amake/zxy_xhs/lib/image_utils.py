"""
图片工具函数
=============
提供图片加载、缩放、合成等通用操作。

所有函数均基于 torch.Tensor (B,H,W,C) 格式，
与 ComfyUI 的 IMAGE 类型直接兼容。
"""

from __future__ import annotations

import numpy as np
import torch
from PIL import Image, ImageDraw, ImageFont, ImageFilter


def tensor_to_pil(image: torch.Tensor) -> Image.Image:
    """将 ComfyUI 的 IMAGE tensor (B,H,W,C) 转换为 PIL Image。

    注意: 如果 B=1 会自动去除 batch 维度；B>1 时只取第一张。
    """
    arr = image.cpu().numpy()
    # 去除多余的 batch 维度: (1, H, W, C) -> (H, W, C)
    if arr.ndim == 4 and arr.shape[0] == 1:
        arr = arr.squeeze(0)
    i = np.clip(255.0 * arr, 0, 255).astype(np.uint8)
    return Image.fromarray(i)


def pil_to_tensor(image: Image.Image) -> torch.Tensor:
    """将 PIL Image 转换为 ComfyUI 的 IMAGE tensor (1,H,W,C)。"""
    arr = np.array(image).astype(np.float32) / 255.0
    return torch.from_numpy(arr)[None,]


def resize_image(
    image: torch.Tensor,
    width: int,
    height: int,
    method: str = "lanczos",
) -> torch.Tensor:
    """调整图片尺寸，返回 (B,H,W,C) tensor。

    Args:
        image: 输入图片 (B,H,W,C)
        width: 目标宽度
        height: 目标高度
        method: 缩放方法 (lanczos/bilinear/bicubic/nearest)

    Returns:
        缩放后的图片 (B,H,W,C)
    """
    if method == "lanczos":
        pil_method = Image.LANCZOS
    elif method == "bilinear":
        pil_method = Image.BILINEAR
    elif method == "bicubic":
        pil_method = Image.BICUBIC
    else:
        pil_method = Image.NEAREST

    batch = []
    for i in range(image.shape[0]):
        pil = tensor_to_pil(image[i : i + 1])
        resized = pil.resize((width, height), pil_method)
        batch.append(pil_to_tensor(resized))
    return torch.cat(batch, dim=0)


def composite_image(
    background: torch.Tensor,
    overlay: torch.Tensor,
    x: int = 0,
    y: int = 0,
    mask: torch.Tensor | None = None,
) -> torch.Tensor:
    """将 overlay 合成到 background 的 (x,y) 位置。

    Args:
        background: 底图 (1,H,W,C)
        overlay: 前景图 (1,H,W,C)
        x: 前景左上角 x 坐标
        y: 前景左上角 y 坐标
        mask: 可选遮罩 (1,H,W,1)

    Returns:
        合成后的图片 (1,H,W,C)
    """
    bg_pil = tensor_to_pil(background)
    fg_pil = tensor_to_pil(overlay)

    if mask is not None:
        mask_pil = tensor_to_pil(mask).convert("L")
        bg_pil.paste(fg_pil, (x, y), mask_pil)
    else:
        bg_pil.paste(fg_pil, (x, y))

    return pil_to_tensor(bg_pil)


def create_blank_canvas(
    width: int,
    height: int,
    color: tuple[int, int, int] = (255, 255, 255),
) -> torch.Tensor:
    """创建纯色画布。

    Args:
        width: 画布宽度（像素）
        height: 画布高度（像素）
        color: RGB 颜色值 (0-255)

    Returns:
        画布 tensor (1,H,W,C)
    """
    img = Image.new("RGB", (width, height), color)
    return pil_to_tensor(img)


def draw_text(
    image: torch.Tensor,
    text: str,
    position: tuple[int, int],
    font_path: str | None = None,
    font_size: int = 48,
    color: tuple[int, int, int] = (0, 0, 0),
    max_width: int | None = None,
    line_spacing: int = 8,
) -> torch.Tensor:
    """在图片上绘制文字。

    Args:
        image: 输入图片 (1,H,W,C)
        text: 要绘制的文字
        position: 左上角坐标 (x, y)
        font_path: 字体文件路径，None 使用默认字体
        font_size: 字号
        color: RGB 颜色
        max_width: 最大宽度，超过自动换行
        line_spacing: 行间距

    Returns:
        绘制文字后的图片 (1,H,W,C)
    """
    pil = tensor_to_pil(image)
    draw = ImageDraw.Draw(pil)

    try:
        font = ImageFont.truetype(font_path, font_size) if font_path else ImageFont.load_default()
    except (IOError, OSError):
        font = ImageFont.load_default()

    if max_width:
        lines = _wrap_text(text, font, max_width)
    else:
        lines = text.split("\n")

    x, y = position
    for line in lines:
        draw.text((x, y), line, fill=color, font=font)
        bbox = draw.textbbox((x, y), line, font=font)
        line_height = bbox[3] - bbox[1] + line_spacing
        y += line_height

    return pil_to_tensor(pil)


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    """按最大宽度自动换行。兼容中英文混合文本。"""
    import re
    lines = []
    for paragraph in text.split("\n"):
        if not paragraph:
            lines.append("")
            continue
        # 分割为"单词"：对中文按字符分割，对英文按空格分割
        tokens = re.findall(r"[\u4e00-\u9fff\u3400-\u4dbf\uf900-\ufaff]|[^\s]+|\s+", paragraph)
        current_line = ""
        for token in tokens:
            test_line = current_line + token
            bbox = font.getbbox(test_line)
            if bbox and bbox[2] > max_width and current_line:
                lines.append(current_line)
                current_line = token
            else:
                current_line = test_line
        if current_line:
            lines.append(current_line)
    return lines


def apply_blur(image: torch.Tensor, radius: float = 5.0) -> torch.Tensor:
    """应用高斯模糊。"""
    pil = tensor_to_pil(image)
    blurred = pil.filter(ImageFilter.GaussianBlur(radius=radius))
    return pil_to_tensor(blurred)