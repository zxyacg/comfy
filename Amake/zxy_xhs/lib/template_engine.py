"""
模板引擎
=========
管理小红书图片模板的定义、加载和渲染。

模板格式 (JSON):
{
    "name": "模板名称",
    "width": 1080,
    "height": 1440,
    "background_color": [255, 255, 255],
    "zones": [
        {
            "type": "image",
            "x": 0, "y": 0,
            "width": 1080,
            "height": 1080,
            "fit": "cover"
        },
        {
            "type": "text",
            "x": 60, "y": 1120,
            "width": 960,
            "height": 200,
            "font_size": 48,
            "color": [51, 51, 51],
            "align": "left",
            "max_lines": 3
        },
        {
            "type": "rect",
            "x": 0, "y": 1080,
            "width": 1080,
            "height": 360,
            "color": [245, 245, 245]
        }
    ]
}

性能优化:
    - list_templates 使用 TTL 缓存，避免频繁磁盘扫描
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

import torch

from .image_utils import (
    composite_image,
    create_blank_canvas,
    draw_text,
    resize_image,
)

# ---------------------------------------------------------------------------
# 数据类型
# ---------------------------------------------------------------------------


@dataclass
class Zone:
    """模板中的一块区域。"""
    type: str
    id: str = ""
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    props: dict[str, Any] = field(default_factory=dict)


@dataclass
class Template:
    """完整的模板定义。"""
    name: str
    width: int
    height: int
    background_color: tuple[int, int, int] = (255, 255, 255)
    zones: list[Zone] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Template":
        zones = []
        for z in data.get("zones", []):
            props = {
                k: v
                for k, v in z.items()
                if k not in ("type", "id", "x", "y", "width", "height")
            }
            zones.append(Zone(
                type=z.get("type", "rect"),
                id=z.get("id", ""),
                x=z.get("x", 0),
                y=z.get("y", 0),
                width=z.get("width", 0),
                height=z.get("height", 0),
                props=props,
            ))
        bg = data.get("background_color", [255, 255, 255])
        return cls(
            name=data.get("name", "untitled"),
            width=data.get("width", 1080),
            height=data.get("height", 1440),
            background_color=tuple(bg),
            zones=zones,
        )


# ---------------------------------------------------------------------------
# 模板管理
# ---------------------------------------------------------------------------

_templates_cache: tuple[float, list[dict]] = (0.0, [])
_CACHE_TTL = 2.0


def get_templates_dir() -> str:
    """获取模板目录路径。"""
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tmpl_dir = os.path.join(base, "templates")
    os.makedirs(tmpl_dir, exist_ok=True)
    return tmpl_dir


def list_templates() -> list[dict]:
    """列出所有可用模板的元信息（带 TTL 缓存）。

    缓存 2 秒有效，避免 ComfyUI 频繁刷新节点定义时重复扫描目录。
    """
    global _templates_cache
    now = time.monotonic()
    if now - _templates_cache[0] < _CACHE_TTL:
        return _templates_cache[1]

    tmpl_dir = get_templates_dir()
    results = []
    for fname in sorted(os.listdir(tmpl_dir)):
        if not fname.endswith(".json"):
            continue
        path = os.path.join(tmpl_dir, fname)
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            results.append({
                "file": fname,
                "name": data.get("name", fname),
                "width": data.get("width", 1080),
                "height": data.get("height", 1440),
            })
        except (json.JSONDecodeError, OSError):
            continue

    _templates_cache = (now, results)
    return results


def load_template(template_name: str) -> Template | None:
    """按名称加载模板。"""
    tmpl_dir = get_templates_dir()
    path = os.path.join(tmpl_dir, template_name)
    if not os.path.isfile(path):
        for fname in os.listdir(tmpl_dir):
            if fname.startswith(template_name) and fname.endswith(".json"):
                path = os.path.join(tmpl_dir, fname)
                break
        else:
            return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return Template.from_dict(data)
    except (json.JSONDecodeError, OSError):
        return None


# ---------------------------------------------------------------------------
# 模板渲染
# ---------------------------------------------------------------------------

def render_template(
    template: Template,
    images: list[torch.Tensor] | None = None,
    texts: dict[str, str] | None = None,
    font_path: str | None = None,
) -> torch.Tensor:
    """将内容和模板渲染为最终图片。

    Args:
        template: 模板定义
        images: 可供使用的图片列表
        texts: 文本映射 {"zone_id": "text"}
        font_path: 字体路径

    Returns:
        渲染结果 (1,H,W,C)
    """
    canvas = create_blank_canvas(
        template.width, template.height, template.background_color
    )

    image_idx = 0
    for zone in template.zones:
        if zone.type == "image":
            if images and image_idx < len(images):
                img = resize_image(
                    images[image_idx], zone.width, zone.height, method="cover"
                )
                canvas = composite_image(canvas, img, zone.x, zone.y)
                image_idx += 1

        elif zone.type == "text":
            text = texts.get(zone.id, "") if texts else ""
            if text and zone.id:
                canvas = draw_text(
                    canvas,
                    text,
                    (zone.x, zone.y),
                    font_path=font_path,
                    font_size=zone.props.get("font_size", 48),
                    color=tuple(zone.props.get("color", [51, 51, 51])),
                    max_width=zone.width,
                )

        elif zone.type == "rect":
            color = tuple(zone.props.get("color", [200, 200, 200]))
            rect = create_blank_canvas(zone.width, zone.height, color)
            canvas = composite_image(canvas, rect, zone.x, zone.y)

    return canvas