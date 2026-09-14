"""
XHS 插件测试运行器
===================
用法:
    # 运行独立工具库测试（无需 ComfyUI）
    python run_tests.py lib

    # 运行节点测试（需在 ComfyUI 目录下执行）
    cd E:\\comfyui\\ComfyUI
    python Amake\\zxy_xhs\\run_tests.py nodes

    # 运行所有测试
    python run_tests.py all
"""

import sys
import os
import unittest


def run_lib_tests():
    """运行 lib/ 工具库测试（独立于 ComfyUI）。"""
    test_dir = os.path.join(os.path.dirname(__file__), "tests")
    sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern="test_lib*.py", top_level_dir=test_dir)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_node_tests():
    """运行节点测试（需 ComfyUI 环境）。"""
    # 需从 ComfyUI 根目录调用
    comfyui_root = os.getcwd()
    plugin_dir = os.path.join(comfyui_root, "Amake", "zxy_xhs")
    sys.path.insert(0, plugin_dir)
    test_dir = os.path.join(plugin_dir, "tests")

    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern="test_nodes*.py", top_level_dir=test_dir)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_integration_tests():
    """运行集成测试。"""
    plugin_dir = os.path.join(os.path.dirname(__file__))
    sys.path.insert(0, plugin_dir)
    test_dir = os.path.join(plugin_dir, "tests")
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern="test_integration*.py", top_level_dir=test_dir)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "lib"

    if mode == "lib":
        success = run_lib_tests()
    elif mode == "nodes":
        success = run_node_tests()
    elif mode == "integration":
        success = run_integration_tests()
    elif mode == "all":
        print("=" * 60)
        print("运行工具库测试...")
        print("=" * 60)
        s1 = run_lib_tests()
        print()
        print("=" * 60)
        print("运行集成测试...")
        print("=" * 60)
        s2 = run_integration_tests()
        success = s1 and s2
    else:
        print(f"未知模式: {mode}")
        print("用法: python run_tests.py [lib|nodes|integration|all]")
        sys.exit(1)

    sys.exit(0 if success else 1)