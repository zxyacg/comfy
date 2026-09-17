"""
单元测试 - XHS 工具库
======================
测试 lib/ 下的独立工具函数（无需 ComfyUI 运行时）。
"""

from __future__ import annotations

import sys
import os
import unittest
import json
import tempfile

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.image_utils import (
    create_blank_canvas,
    pil_to_tensor,
    tensor_to_pil,
    resize_image,
    composite_image,
    draw_text,
    apply_blur,
)
from lib.template_engine import (
    Template,
    Zone,
    render_template,
    list_templates,
    get_templates_dir,
)


class TestImageUtils(unittest.TestCase):
    """测试图片工具函数。"""

    def setUp(self):
        self.width, self.height = 100, 100
        self.canvas = create_blank_canvas(self.width, self.height, (255, 255, 255))

    def test_create_blank_canvas_shape(self):
        """验证画布形状为 (1, H, W, 3)。"""
        self.assertEqual(self.canvas.shape, (1, self.height, self.width, 3))

    def test_create_blank_canvas_color(self):
        """白色画布所有像素值应为 1.0。"""
        self.assertTrue(torch.all(self.canvas == 1.0))

    def test_create_red_canvas(self):
        """验证红色画布的 RGB 通道。"""
        red = create_blank_canvas(10, 10, (255, 0, 0))
        self.assertTrue(torch.all(red[0, :, :, 0] == 1.0))
        self.assertTrue(torch.all(red[0, :, :, 1] == 0.0))
        self.assertTrue(torch.all(red[0, :, :, 2] == 0.0))

    def test_tensor_pil_roundtrip(self):
        """验证 tensor -> PIL -> tensor 无损转换（误差 1/255）。"""
        pil = tensor_to_pil(self.canvas)
        back = pil_to_tensor(pil)
        self.assertTrue(torch.allclose(self.canvas, back, atol=1 / 255))

    def test_resize_image_shape(self):
        """验证缩放后形状正确。"""
        resized = resize_image(self.canvas, 50, 50)
        self.assertEqual(resized.shape, (1, 50, 50, 3))

    def test_resize_image_batch(self):
        """验证批量缩放。"""
        batch = torch.cat([self.canvas, self.canvas], dim=0)
        resized = resize_image(batch, 50, 50)
        self.assertEqual(resized.shape, (2, 50, 50, 3))

    def test_composite_image(self):
        """验证图片合成：红色叠加到白色画布。"""
        overlay = create_blank_canvas(50, 50, (255, 0, 0))
        result = composite_image(self.canvas, overlay, 0, 0)
        self.assertTrue(torch.all(result[0, 0, 0] == torch.tensor([1.0, 0.0, 0.0])))
        # 未叠加区域应保持白色
        self.assertTrue(torch.all(result[0, 0, 60] == torch.tensor([1.0, 1.0, 1.0])))

    def test_draw_text_basic(self):
        """验证文字绘制不报错且形状不变。"""
        result = draw_text(self.canvas, "测试文字", (10, 10), font_size=20)
        self.assertEqual(result.shape, self.canvas.shape)

    def test_draw_text_empty(self):
        """空文字不应修改图片。"""
        result = draw_text(self.canvas, "", (10, 10))
        self.assertTrue(torch.allclose(self.canvas, result))

    def test_draw_text_multiline(self):
        """验证多行文字。"""
        result = draw_text(self.canvas, "第一行\n第二行", (10, 10))
        self.assertEqual(result.shape, self.canvas.shape)

    def test_apply_blur(self):
        """验证高斯模糊。"""
        result = apply_blur(self.canvas, radius=2.0)
        self.assertEqual(result.shape, self.canvas.shape)


class TestTemplateEngine(unittest.TestCase):
    """测试模板引擎。"""

    def test_template_from_dict(self):
        """验证从字典加载模板。"""
        data = {
            "name": "测试模板",
            "width": 1080,
            "height": 1440,
            "background_color": [255, 255, 255],
            "zones": [
                {"id": "img1", "type": "image", "x": 0, "y": 0, "width": 500, "height": 500},
                {"id": "txt1", "type": "text", "x": 10, "y": 10, "width": 200, "height": 50},
            ],
        }
        tmpl = Template.from_dict(data)
        self.assertEqual(tmpl.name, "测试模板")
        self.assertEqual(tmpl.width, 1080)
        self.assertEqual(tmpl.height, 1440)
        self.assertEqual(len(tmpl.zones), 2)
        self.assertEqual(tmpl.zones[0].type, "image")
        self.assertEqual(tmpl.zones[1].type, "text")

    def test_template_defaults(self):
        """验证模板默认值。"""
        tmpl = Template.from_dict({"name": "默认模板"})
        self.assertEqual(tmpl.width, 1080)
        self.assertEqual(tmpl.height, 1440)
        self.assertEqual(tmpl.background_color, (255, 255, 255))

    def test_render_empty_template(self):
        """验证空模板渲染。"""
        tmpl = Template("空白", 100, 100)
        result = render_template(tmpl)
        self.assertEqual(result.shape, (1, 100, 100, 3))
        self.assertTrue(torch.all(result == 1.0))  # 白色

    def test_render_rect_zone(self):
        """验证矩形区域渲染。"""
        tmpl = Template(
            "矩形测试", 100, 100, (255, 255, 255),
            [Zone("rect", "bg", 10, 10, 50, 50, {"color": [255, 0, 0]})],
        )
        result = render_template(tmpl)
        # 矩形区域内为红色
        self.assertTrue(torch.all(result[0, 20, 20] == torch.tensor([1.0, 0.0, 0.0])))
        # 矩形区域外为白色
        self.assertTrue(torch.all(result[0, 0, 0] == torch.tensor([1.0, 1.0, 1.0])))

    def test_render_with_image_zone(self):
        """验证图片区域渲染。"""
        tmpl = Template(
            "图片测试", 100, 100,
            zones=[Zone("image", "img", 0, 0, 100, 100)],
        )
        img = create_blank_canvas(100, 100, (0, 255, 0))
        result = render_template(tmpl, images=[img])
        self.assertTrue(torch.all(result[0, 50, 50] == torch.tensor([0.0, 1.0, 0.0])))

    def test_render_multi_image(self):
        """验证多图片渲染（顺序填充）。"""
        tmpl = Template(
            "多图测试", 200, 100,
            zones=[
                Zone("image", "left", 0, 0, 100, 100),
                Zone("image", "right", 100, 0, 100, 100),
            ],
        )
        img1 = create_blank_canvas(100, 100, (255, 0, 0))
        img2 = create_blank_canvas(100, 100, (0, 0, 255))
        result = render_template(tmpl, images=[img1, img2])
        self.assertTrue(torch.all(result[0, 50, 50] == torch.tensor([1.0, 0.0, 0.0])))
        self.assertTrue(torch.all(result[0, 50, 150] == torch.tensor([0.0, 0.0, 1.0])))

    def test_render_with_text(self):
        """验证文字区域渲染不报错。"""
        tmpl = Template(
            "文字测试", 200, 200,
            zones=[Zone("text", "txt", 10, 10, 180, 50, {"id": "title", "font_size": 24})],
        )
        # id 属性设置在 zone 上
        result = render_template(tmpl, texts={"title": "Hello"})
        self.assertEqual(result.shape, (1, 200, 200, 3))

    def test_list_templates(self):
        """验证 list_templates 不报错且返回列表。"""
        templates = list_templates()
        self.assertIsInstance(templates, list)

    def test_list_templates_cache_hit(self):
        """验证 list_templates TTL 缓存：2秒内连续调用返回同一对象。"""
        t1 = list_templates()
        t2 = list_templates()
        self.assertIs(t1, t2, "TTL 缓存未生效，连续调用应返回同一列表对象")


class TestRecipeCompliance(unittest.TestCase):
    """配方合规性检查。"""

    def _count_lines(self, rel_path: str) -> int:
        base = os.path.join(os.path.dirname(__file__), "..")
        full = os.path.join(base, rel_path)
        with open(full, "r", encoding="utf-8") as f:
            return sum(1 for _ in f)

    def test_image_utils_under_300_lines(self):
        self.assertLessEqual(self._count_lines("lib/image_utils.py"), 300)

    def test_template_engine_under_300_lines(self):
        self.assertLessEqual(self._count_lines("lib/template_engine.py"), 300)

    def test_image_loader_under_300_lines(self):
        self.assertLessEqual(self._count_lines("nodes/image_loader.py"), 300)

    def test_canvas_under_300_lines(self):
        self.assertLessEqual(self._count_lines("nodes/canvas.py"), 300)

    def test_template_under_300_lines(self):
        self.assertLessEqual(self._count_lines("nodes/template.py"), 300)

    def test_text_overlay_under_300_lines(self):
        self.assertLessEqual(self._count_lines("nodes/text_overlay.py"), 300)

    def test_exporter_under_300_lines(self):
        self.assertLessEqual(self._count_lines("nodes/exporter.py"), 300)

    def test_workbench_js_under_300_lines(self):
        self.assertLessEqual(self._count_lines("web/xhs_workbench.js"), 300)


if __name__ == "__main__":
    unittest.main(verbosity=2)