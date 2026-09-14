"""
XHS Template - 模板节点
========================
应用小红书图片模板，将内容和模板合成为最终图片。

功能:
    - 从模板库选择模板
    - 自动按模板定义渲染
    - 支持图片填充和文字叠加
    - 批量处理

工作流程:
    1. 选择模板 -> 2. 提供图片 -> 3. 提供文字 -> 4. 渲染输出
"""

from __future__ import annotations

import torch

from ..lib.template_engine import (
    list_templates,
    load_template,
    render_template,
)

_CATEGORY = "XHS Tools"


def _get_template_names() -> list[str]:
    """获取可用模板名称列表（下拉菜单用）。"""
    templates = list_templates()
    if not templates:
        return ["(无模板，请先在 templates/ 中添加)"]
    return [t["name"] for t in templates]


class XHSTemplate:
    """应用小红书模板到图片上。"""

    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {
            "required": {
                "template_name": (_get_template_names(), {
                    "tooltip": "选择要应用的模板",
                }),
                "images": ("IMAGE", {
                    "tooltip": "要填充到模板中的图片",
                }),
                "title_text": ("STRING", {
                    "default": "",
                    "multiline": False,
                    "tooltip": "标题文字",
                }),
                "content_text": ("STRING", {
                    "default": "",
                    "multiline": True,
                    "tooltip": "正文内容",
                }),
                "font_size": ("INT", {
                    "default": 48, "min": 12, "max": 200, "step": 1,
                    "tooltip": "正文字号",
                }),
            },
            "optional": {
                "title_size": ("INT", {
                    "default": 72, "min": 12, "max": 200, "step": 1,
                    "tooltip": "标题字号",
                }),
            },
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("image",)
    OUTPUT_IS_LIST = (False,)
    FUNCTION = "apply_template"
    CATEGORY = _CATEGORY
    DESCRIPTION = "将图片和文字渲染到小红书模板中"

    def apply_template(
        self,
        template_name: str,
        images: torch.Tensor,
        title_text: str = "",
        content_text: str = "",
        font_size: int = 48,
        title_size: int = 72,
    ) -> tuple[torch.Tensor]:
        """应用模板渲染。"""
        template = load_template(template_name)
        if template is None:
            raise RuntimeError(f"找不到模板: {template_name}")

        # 构建文本映射（依模板 zone id 匹配）
        texts = {}
        for zone in template.zones:
            if zone.type == "text":
                if zone.id == "title" and title_text:
                    texts[zone.id] = title_text
                elif zone.id == "content" and content_text:
                    texts[zone.id] = content_text
                elif zone.id == "tag" and title_text:
                    texts[zone.id] = title_text

        # 将每张图片独立渲染
        results = []
        for i in range(images.shape[0]):
            img = images[i : i + 1]
            result = render_template(
                template,
                images=[img],
                texts=texts,
            )
            results.append(result)

        return (torch.cat(results, dim=0),)

    @classmethod
    def IS_CHANGED(cls, template_name: str, **kwargs) -> bool:
        """检测模板是否有变化以决定是否重执行。"""
        return template_name