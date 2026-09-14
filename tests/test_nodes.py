"""
节点单元测试 - 需在 ComfyUI 环境下运行
========================================
测试节点类的 INPUT_TYPES / RETURN_TYPES / CATEGORY 等元信息。

运行方式:
    cd E:\\comfyui\\ComfyUI
    python -m pytest Amake\\zxy_xhs\\tests\\test_nodes.py -v
    或:
    python -m unittest Amake.zxy_xhs.tests.test_nodes -v
"""

from __future__ import annotations

import sys
import os
import unittest

# 确保 ComfyUI 根目录在路径中
_COMFYUI_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _COMFYUI_ROOT not in sys.path:
    sys.path.insert(0, _COMFYUI_ROOT)


class TestNodeRegistration(unittest.TestCase):
    """测试节点注册信息（不依赖 ComfyUI 运行时）。"""

    @classmethod
    def setUpClass(cls):
        """延迟导入，确保路径已设置。"""
        from nodes import NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
        cls.mappings = NODE_CLASS_MAPPINGS
        cls.display_names = NODE_DISPLAY_NAME_MAPPINGS

    def test_all_nodes_registered(self):
        """验证所有节点已注册。"""
        expected = {
            "XHSImageLoader",
            "XHSCanvas",
            "XHSTemplate",
            "XHSTextOverlay",
            "XHSExport",
        }
        self.assertTrue(expected.issubset(set(self.mappings.keys())))

    def test_all_display_names(self):
        """验证所有节点有显示名称。"""
        for node_id in self.mappings:
            self.assertIn(node_id, self.display_names,
                          f"{node_id} 缺少 NODE_DISPLAY_NAME_MAPPINGS")


class TestNodeInterface(unittest.TestCase):
    """测试节点接口定义。"""

    @classmethod
    def setUpClass(cls):
        from nodes import NODE_CLASS_MAPPINGS
        cls.mappings = NODE_CLASS_MAPPINGS

    def test_each_node_has_required_attributes(self):
        """验证每个节点有必要的类属性。"""
        for name, node_cls in self.mappings.items():
            with self.subTest(node=name):
                self.assertTrue(hasattr(node_cls, "INPUT_TYPES"),
                                f"{name} 缺少 INPUT_TYPES")
                self.assertTrue(hasattr(node_cls, "RETURN_TYPES"),
                                f"{name} 缺少 RETURN_TYPES")
                self.assertTrue(hasattr(node_cls, "FUNCTION"),
                                f"{name} 缺少 FUNCTION")
                self.assertTrue(hasattr(node_cls, "CATEGORY"),
                                f"{name} 缺少 CATEGORY")

    def test_input_types_valid(self):
        """验证 INPUT_TYPES 返回值格式正确。"""
        for name, node_cls in self.mappings.items():
            with self.subTest(node=name):
                try:
                    input_types = node_cls.INPUT_TYPES()
                    self.assertIn("required", input_types)
                except Exception as e:
                    self.fail(f"{name}.INPUT_TYPES() 抛出异常: {e}")

    def test_return_types_non_empty(self):
        """验证 RETURN_TYPES 非空。"""
        for name, node_cls in self.mappings.items():
            with self.subTest(node=name):
                self.assertTrue(len(node_cls.RETURN_TYPES) > 0)

    def test_category_prefix(self):
        """验证所有节点 CATEGORY 以 'XHS' 开头。"""
        for name, node_cls in self.mappings.items():
            with self.subTest(node=name):
                self.assertTrue(
                    node_cls.CATEGORY.startswith("XHS"),
                    f"{name} 的 CATEGORY 应为 XHS 开头，实际为 {node_cls.CATEGORY}",
                )


class TestXHSCanvasNode(unittest.TestCase):
    """测试 XHSCanvas 节点（需 ComfyUI 可用）。"""

    @classmethod
    def setUpClass(cls):
        from nodes import NODE_CLASS_MAPPINGS
        cls.node_cls = NODE_CLASS_MAPPINGS.get("XHSCanvas")

    def test_node_exists(self):
        self.assertIsNotNone(self.node_cls)

    def test_has_preset_input(self):
        inputs = self.node_cls.INPUT_TYPES()
        self.assertIn("preset", inputs["required"])

    def test_preset_options(self):
        inputs = self.node_cls.INPUT_TYPES()
        preset = inputs["required"]["preset"]
        options = preset[0]
        self.assertIn("竖版 3:4 (1080x1440)", options)
        self.assertIn("自定义", options)

    def test_parse_hex_color(self):
        from nodes.canvas import XHSCanvas
        self.assertEqual(XHSCanvas._parse_hex_color("#FF0000"), (255, 0, 0))
        self.assertEqual(XHSCanvas._parse_hex_color("00FF00"), (0, 255, 0))
        self.assertEqual(XHSCanvas._parse_hex_color("#FFF"), (255, 255, 255))


class TestXHSTextOverlayNode(unittest.TestCase):
    """测试 XHSTextOverlay 节点。"""

    @classmethod
    def setUpClass(cls):
        from nodes import NODE_CLASS_MAPPINGS
        cls.node_cls = NODE_CLASS_MAPPINGS.get("XHSTextOverlay")

    def test_node_exists(self):
        self.assertIsNotNone(self.node_cls)

    def test_hex_color_parsing(self):
        from nodes.text_overlay import XHSTextOverlay
        self.assertEqual(XHSTextOverlay._parse_hex("#FF6B81"), (255, 107, 129))


class TestXHSExportNode(unittest.TestCase):
    """测试 XHSExport 节点。"""

    @classmethod
    def setUpClass(cls):
        from nodes import NODE_CLASS_MAPPINGS
        cls.node_cls = NODE_CLASS_MAPPINGS.get("XHSExport")

    def test_node_exists(self):
        self.assertIsNotNone(self.node_cls)

    def test_is_output_node(self):
        self.assertTrue(getattr(self.node_cls, "OUTPUT_NODE", False))


if __name__ == "__main__":
    unittest.main(verbosity=2)