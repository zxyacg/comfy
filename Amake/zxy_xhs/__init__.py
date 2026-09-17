"""
小红书图文批量生成插件 - XHS Workflow Nodes
=============================================
ComfyUI 插件，用于批量生成小红书图文内容。
各节点职责单一，低耦合，可扩展。

设计理念:
    - 每个节点只做一件事
    - 通过节点组合实现复杂工作流
    - 支持模板化批量处理
"""

from .nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS

WEB_DIRECTORY = "./web"

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]