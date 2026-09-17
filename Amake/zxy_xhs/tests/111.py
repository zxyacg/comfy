"""
测试 XHSImageLoader.load_image
===============================
Mock ComfyUI 依赖 (folder_paths, node_helpers) 来测试图片加载逻辑。

运行方式:
    cd E:\comfyui\ComfyUI
    python -m pytest Amake\\zxy_xhs\\tests\\test_image_loader.py -v
    或:
    python -m unittest Amake.zxy_xhs.tests.test_image_loader -v
"""

from __future__ import annotations

import sys
import os
import io
import unittest
from unittest.mock import patch, MagicMock

import torch
import numpy as np
from PIL import Image, ImageOps

# 确保 ComfyUI 根目录在路径中
_COMFYUI_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..")
)
if _COMFYUI_ROOT not in sys.path:
    sys.path.insert(0, _COMFYUI_ROOT)

class TestXHSImageLoaderLoadImage(unittest.TestCase):
    """测试 XHSImageLoader.load_image 方法。"""

    def setUp(self):
        """每个测试前延迟导入并准备 mock。"""
        from nodes.image_loader import XHSImageLoader
        self.loader = XHSImageLoader()

        # ------ mock folder_paths.get_annotated_filepath ------
        self._filepath_patcher = patch(
            "nodes.image_loader.folder_paths.get_annotated_filepath"
        )
        self.mock_get_path = self._filepath_patcher.start()
        self.mock_get_path.return_value = r"C:\fake\input\test.png"

        # ------ mock node_helpers.pillow ------
        #   node_helpers.pillow(fn, arg) 等价于 fn(arg)
        #   我们让它直接调用 fn(arg) 即可
        self._pillow_patcher = patch(
            "nodes.image_loader.node_helpers.pillow",
            side_effect=lambda fn, arg: fn(arg),
        )
        self._pillow_patcher.start()

    def tearDown(self):
        self._filepath_patcher.stop()
        self._pillow_patcher.stop()

    # ========== 辅助方法 ==========

    @staticmethod
    def _make_image(mode: str, size=(64, 64), color=None) -> Image.Image:
        """创建一张纯色 PIL Image。"""
        if color is None:
            color = (100, 150, 200, 255) if mode == "RGBA" else (100, 150, 200)
        return Image.new(mode, size, color)

    # ========== 基本加载 ==========

    def test_load_rgb_image(self):
        """加载 RGB 图片应返回正确的 tensor 形状。"""
        img = self._make_image("RGB", (32, 48))

        with patch("PIL.Image.open", return_value=img):
            images, mask = self.loader.load_image("test.png")

        # IMAGE: (1, H, W, 3)
        self.assertIsInstance(images, torch.Tensor)
        self.assertEqual(images.shape, (1, 48, 32, 3))
        self.assertAlmostEqual(images[0, 0, 0, 0].item(), 100.0 / 255)

        # MASK: RGB 图片应生成全白 mask
        self.assertIsInstance(mask, torch.Tensor)
        self.assertEqual(mask.shape, (1, 64, 64))
        self.assertTrue(torch.all(mask == 1.0))

    def test_load_rgba_image(self):
        """加载 RGBA 图片应提取 alpha 通道作为 mask。"""
        # 半透明红色：RGB(255,0,0) + Alpha(128)
        rgba = Image.new("RGBA", (16, 16), (255, 0, 0, 128))

        with patch("PIL.Image.open", return_value=rgba):
            images, mask = self.loader.load_image("rgba.png")

        self.assertEqual(images.shape, (1, 16, 16, 3))
        # RGB 通道：红色分量应为 1.0
        self.assertAlmostEqual(images[0, 0, 0, 0].item(), 1.0)
        # Alpha mask：128/255 ≈ 0.502
        self.assertAlmostEqual(mask[0, 0, 0].item(), 128.0 / 255, places=4)

    def test_load_grayscale_image(self):
        """加载灰度图 (L) 应转为 RGB 三通道并生成全白 mask。"""
        gray = Image.new("L", (20, 30), 128)

        with patch("PIL.Image.open", return_value=gray):
            images, mask = self.loader.load_image("gray.png")

        self.assertEqual(images.shape, (1, 30, 20, 3))
        # 三个通道值应相同
        self.assertTrue(torch.allclose(
            images[0, 0, 0, :],
            torch.tensor([128.0 / 255] * 3),
            atol=1 / 255,
        ))

    def test_load_mode_I_image(self):
        """模式 I (32-bit int) 应缩放 0.04 后转为 L。"""
        arr = np.full((10, 10), 10000, dtype=np.int32)
        mode_i = Image.fromarray(arr, mode="I")

        with patch("PIL.Image.open", return_value=mode_i):
            images, mask = self.loader.load_image("mode_i.png")

        self.assertEqual(images.shape, (1, 10, 10, 3))
        # 10000 * 0.04 = 400, 400/255 ≈ 1.0
        self.assertAlmostEqual(images[0, 0, 0, 0].item(), 1.0, places=4)

    # ========== 缩放测试 ==========

    def test_resize_valid(self):
        """指定 target_width/height 应缩放图片。"""
        img = self._make_image("RGB", (100, 200))

        with patch("PIL.Image.open", return_value=img):
            images, _ = self.loader.load_image(
                "test.png", target_width=50, target_height=40
            )

        self.assertEqual(images.shape, (1, 40, 50, 3))

    def test_resize_zero_skips(self):
        """target_width=0 或 target_height=0 应跳过缩放。"""
        img = self._make_image("RGB", (80, 60))

        with patch("PIL.Image.open", return_value=img):
            images, _ = self.loader.load_image(
                "test.png", target_width=0, target_height=100
            )

        # width=0 → 跳过缩放，保持原尺寸
        self.assertEqual(images.shape, (1, 60, 80, 3))

    def test_resize_both_zero(self):
        """target_width=0 且 target_height=0 应保持原尺寸。"""
        img = self._make_image("RGB", (55, 77))

        with patch("PIL.Image.open", return_value=img):
            images, _ = self.loader.load_image("test.png")

        self.assertEqual(images.shape, (1, 77, 55, 3))

    # ========== GIF 多帧测试 ==========

    def test_load_gif_multi_frame(self):
        """GIF 多帧应返回 batch tensor。"""
        frames = [
            Image.new("RGB", (10, 10), (255, 0, 0)),
            Image.new("RGB", (10, 10), (0, 255, 0)),
            Image.new("RGB", (10, 10), (0, 0, 255)),
        ]
        buf = io.BytesIO()
        frames[0].save(
            buf, format="GIF",
            save_all=True,
            append_images=frames[1:],
            loop=0,
        )
        buf.seek(0)
        gif = Image.open(buf)

        with patch("PIL.Image.open", return_value=gif):
            images, mask = self.loader.load_image("anim.gif")

        self.assertEqual(images.shape, (3, 10, 10, 3))
        self.assertTrue(torch.all(
            images[0, 0, 0] == torch.tensor([1.0, 0.0, 0.0])
        ))
        self.assertTrue(torch.all(
            images[1, 0, 0] == torch.tensor([0.0, 1.0, 0.0])
        ))
        self.assertTrue(torch.all(
            images[2, 0, 0] == torch.tensor([0.0, 0.0, 1.0])
        ))

    # ========== 异常测试 ==========

    def test_file_not_found_raises(self):
        """文件不存在应抛出异常。"""
        self.mock_get_path.return_value = r"C:\nonexistent\file.png"

        with self.assertRaises(Exception):
            with patch("PIL.Image.open", side_effect=FileNotFoundError("No such file")):
                self.loader.load_image("missing.png")

    def test_invalid_image_raises(self):
        """损坏的图片文件应抛出异常。"""
        self.mock_get_path.return_value = r"C:\fake\corrupt.png"

        with self.assertRaises(Exception):
            with patch("PIL.Image.open", side_effect=OSError("cannot identify image file")):
                self.loader.load_image("corrupt.png")

    # ========== 输出类型与范围 ==========

    def test_image_tensor_range(self):
        """IMAGE tensor 应在 [0, 1] 范围内。"""
        img = self._make_image("RGB", (8, 8), (255, 128, 0))

        with patch("PIL.Image.open", return_value=img):
            images, _ = self.loader.load_image("test.png")

        self.assertGreaterEqual(images.min().item(), 0.0)
        self.assertLessEqual(images.max().item(), 1.0)

    def test_mask_tensor_range(self):
        """MASK tensor 应在 [0, 1] 范围内。"""
        rgba = Image.new("RGBA", (8, 8), (0, 0, 0, 200))

        with patch("PIL.Image.open", return_value=rgba):
            _, mask = self.loader.load_image("rgba.png")

        self.assertGreaterEqual(mask.min().item(), 0.0)
        self.assertLessEqual(mask.max().item(), 1.0)

    # ========== EXIF 自动旋转 ==========

    def test_exif_orientation_applied(self):
        """含 EXIF 方向标签的图片应自动旋转。"""
        img = Image.new("RGB", (20, 40), (255, 0, 0))
        exif_data = img.getexif()
        exif_data[0x0112] = 6  # Orientation: Rotate 90 CW

        buf = io.BytesIO()
        img.save(buf, format="JPEG", exif=exif_data.tobytes())
        buf.seek(0)
        rotated = Image.open(buf)

        with patch("PIL.Image.open", return_value=rotated):
            images, _ = self.loader.load_image("exif.jpg")

        self.assertEqual(
            images.shape,
            (1, 20, 40, 3),
            "EXIF Orientation=6 应将 20x40 旋转为 40x20",
        )

if __name__ == "__main__":
    unittest.main(verbosity=2)