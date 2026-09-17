"""
集成测试 - XHS 工作流
=======================
测试 lib/ 工具库组合的完整工作流（无需 ComfyUI 运行时）。
"""

from __future__ import annotations

import sys
import os
import unittest
import tempfile

import torch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from lib.image_utils import (
    create_blank_canvas,
    resize_image,
    composite_image,
    draw_text,
    pil_to_tensor,
    tensor_to_pil,
)
from lib.template_engine import Template, Zone, render_template, list_templates


class TestCanvasToTextWorkflow(unittest.TestCase):
    """画布 -> 文字叠加 完整工作流。"""

    def test_create_canvas_and_add_text(self):
        """创建画布 -> 添加标题 -> 添加正文。"""
        # Step 1: 创建画布（1080x1440 竖版）
        canvas = create_blank_canvas(1080, 1440, (255, 255, 255))
        self.assertEqual(canvas.shape, (1, 1440, 1080, 3))

        # Step 2: 叠加标题
        with_title = draw_text(
            canvas, "设计模式学习笔记", (60, 1120),
            font_size=64, color=(51, 51, 51), max_width=960,
        )
        self.assertEqual(with_title.shape, canvas.shape)

        # Step 3: 叠加正文
        final = draw_text(
            with_title,
            "良好的架构是设计出来的，不是重构出来的。",
            (60, 1220), font_size=40, color=(102, 102, 102), max_width=960,
        )
        self.assertEqual(final.shape, canvas.shape)
        # 文字叠加后画布应变化
        self.assertFalse(torch.allclose(canvas, final))

    def test_text_multiline_wrap(self):
        """验证自动换行。"""
        canvas = create_blank_canvas(400, 400, (255, 255, 255))
        long_text = "这是一段很长的文字，它应该会在达到最大宽度时自动换行。"
        result = draw_text(canvas, long_text, (20, 20), font_size=24, max_width=360)
        self.assertEqual(result.shape, canvas.shape)


class TestTemplateWorkflow(unittest.TestCase):
    """模板渲染工作流。"""

    def test_template_with_image_and_text(self):
        """模板 + 图片 + 文字 完整流程。"""
        tmpl = Template(
            name="测试模板",
            width=300, height=300,
            background_color=(248, 248, 248),
            zones=[
                Zone("rect", "bg", 0, 0, 300, 300, {"color": [248, 248, 248]}),
                Zone("image", "img", 20, 20, 260, 200),
                Zone("text", "title", 20, 240, 260, 40,
                     {"font_size": 24, "color": [51, 51, 51]}),
            ],
        )
        # 设置 text zone 的 id
        tmpl.zones[2].id = "title_text"

        image = create_blank_canvas(260, 200, (200, 200, 255))
        result = render_template(tmpl, images=[image], texts={"title_text": "标题内容"})

        self.assertEqual(result.shape, (1, 300, 300, 3))
        # 图片区域应为蓝紫色
        self.assertTrue(torch.all(result[0, 100, 100][:2] >= torch.tensor([200.0/255, 200.0/255])))

    def test_multi_image_template(self):
        """多图片模板。"""
        tmpl = Template(
            name="多图模板",
            width=300, height=100,
            zones=[
                Zone("image", "left", 0, 0, 100, 100),
                Zone("image", "mid", 100, 0, 100, 100),
                Zone("image", "right", 200, 0, 100, 100),
            ],
        )
        imgs = [
            create_blank_canvas(100, 100, (255, 0, 0)),
            create_blank_canvas(100, 100, (0, 255, 0)),
            create_blank_canvas(100, 100, (0, 0, 255)),
        ]
        result = render_template(tmpl, images=imgs)
        self.assertEqual(result.shape, (1, 100, 300, 3))

        # 验证三图片位置颜色
        mid_h = 50
        self.assertTrue(torch.all(result[0, mid_h, 50] == torch.tensor([1.0, 0.0, 0.0])))
        self.assertTrue(torch.all(result[0, mid_h, 150] == torch.tensor([0.0, 1.0, 0.0])))
        self.assertTrue(torch.all(result[0, mid_h, 250] == torch.tensor([0.0, 0.0, 1.0])))

    def test_rect_and_text_combo(self):
        """矩形背景 + 文字 组合渲染。"""
        tmpl = Template(
            name="卡片模板",
            width=400, height=200,
            zones=[
                Zone("rect", "header", 0, 0, 400, 60, {"color": [255, 100, 100]}),
                Zone("text", "heading", 20, 10, 360, 40,
                     {"font_size": 28, "color": [255, 255, 255]}),
            ],
        )
        tmpl.zones[1].id = "heading"
        result = render_template(tmpl, texts={"heading": "小红书标题"})
        self.assertEqual(result.shape, (1, 200, 400, 3))
        # header 区域为红色
        self.assertTrue(torch.all(result[0, 30, 30] == torch.tensor([1.0, 100.0/255, 100.0/255])))


class TestExportCompatibility(unittest.TestCase):
    """导出兼容性测试。"""

    def test_pil_roundtrip_preserves_content(self):
        """PIL -> Tensor -> PIL 的往返转换应保持内容。"""
        canvas = create_blank_canvas(100, 100, (255, 128, 64))
        pil = tensor_to_pil(canvas)
        back = pil_to_tensor(pil)
        self.assertTrue(torch.allclose(canvas, back, atol=1/255))

    def test_tensor_to_pil_shape(self):
        """PIL 转换后尺寸正确。"""
        canvas = create_blank_canvas(200, 150, (0, 0, 0))
        pil = tensor_to_pil(canvas)
        self.assertEqual(pil.size, (200, 150))

    def test_batch_pil_roundtrip(self):
        """批量 tensor 的 PIL 转换。"""
        batch = torch.cat([
            create_blank_canvas(50, 50, (255, 0, 0)),
            create_blank_canvas(50, 50, (0, 255, 0)),
        ], dim=0)
        # 测试取第一张
        pil0 = tensor_to_pil(batch[0:1])
        pil1 = tensor_to_pil(batch[1:2])
        self.assertEqual(pil0.size, (50, 50))
        self.assertEqual(pil1.size, (50, 50))


class TestCachePerformance(unittest.TestCase):
    """缓存性能验证。"""

    def test_list_templates_cache_speedup(self):
        """验证 list_templates 缓存后连续调用更快。"""
        import time

        list_templates()

        start = time.monotonic()
        for _ in range(100):
            list_templates()
        cached_elapsed = time.monotonic() - start

        self.assertLess(
            cached_elapsed, 0.1,
            f"100次缓存调用耗时 {cached_elapsed:.4f}s，应 < 0.1s",
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)