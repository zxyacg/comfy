"""
XHS 节点模块
=============
聚合所有 XHS 节点的注册映射。
"""

from .image_loader import XHSImageLoader
from .canvas import XHSCanvas
from .template import XHSTemplate
from .text_overlay import XHSTextOverlay
from .exporter import XHSExport

NODE_CLASS_MAPPINGS = {
    "XHSImageLoader": XHSImageLoader,
    "XHSCanvas": XHSCanvas,
    "XHSTemplate": XHSTemplate,
    "XHSTextOverlay": XHSTextOverlay,
    "XHSExport": XHSExport,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "XHSImageLoader": "XHS Image Loader",
    "XHSCanvas": "XHS Canvas",
    "XHSTemplate": "XHS Template",
    "XHSTextOverlay": "XHS Text Overlay",
    "XHSExport": "XHS Export",
}