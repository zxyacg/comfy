# 项目文件地图

## 入口与注册

| 文件 | 职责 | 分类 |
|------|------|------|
| `__init__.py` | 插件入口，导出 `NODE_CLASS_MAPPINGS`、`NODE_DISPLAY_NAME_MAPPINGS`、`WEB_DIRECTORY` | **核心：不可随意修改** |

## 节点层 (`nodes/`)

> 每个节点文件独立，不互相依赖。

| 文件 | 行数 | 职责 | 分类 |
|------|------|------|------|
| `__init__.py` | 24 | 聚合注册全部 5 个节点 + 1 个简化版 | **核心** |
| `image_loader.py` | 151 | `XHSImageLoader` + `XHSImageLoaderSimple`：从 ComfyUI input 目录加载图片 | 业务逻辑 |
| `canvas.py` | 102 | `XHSCanvas`：创建空白画布，支持预设/自定义尺寸和 HEX 颜色 | 业务逻辑 |
| `template.py` | 121 | `XHSTemplate`：选择模板，渲染图片+文字 | 业务逻辑 |
| `text_overlay.py` | 127 | `XHSTextOverlay`：在图片上叠加文字，支持中文自动换行 | 业务逻辑 |
| `exporter.py` | 124 | `XHSExport`：批量导出图片到 output 目录，支持 PNG/JPEG + 元数据 | 业务逻辑 |

## 工具层 (`lib/`)

> **基础设施：不可随意修改**。所有节点依赖此层。

| 文件 | 行数 | 职责 | 分类 |
|------|------|------|------|
| `__init__.py` | 5 | 模块标记 | 基础设施 |
| `image_utils.py` | 196 | 核心图片处理：tensor↔PIL 转换、缩放、合成、画布创建、文字绘制、模糊 | **核心基础设施** |
| `template_engine.py` | 211 | 模板引擎：Template/Zone 数据结构、模板加载/列表、渲染引擎 | **核心基础设施** |

## 模板数据 (`templates/`)

| 文件 | 职责 | 分类 |
|------|------|------|
| `classic_card.json` | "经典卡片"模板：上图片 + 下标题+正文 | 数据（可扩展） |
| `clean_quote.json` | "简约语录"模板：上图+下白底+语录+标签 | 数据（可扩展） |

## 前端 (`web/`)

| 文件 | 行数 | 职责 | 分类 |
|------|------|------|------|
| `__init__.py` | 1 | 模块标记 | UI |
| `xhs_workbench.js` | 78 | XHS 节点粉色主题 + 预览/信息/按钮增强 | UI |

## 测试套件 (`tests/`)

| 文件 | 行数 | 职责 | 运行要求 |
|------|------|------|---------|
| `__init__.py` | 1 | 包标记 | — |
| `test_lib.py` | 196 | 19 项测试：image_utils + template_engine | 独立运行 |
| `test_integration.py` | 162 | 8 项集成测试：完整工作流 | 独立运行 |
| `test_nodes.py` | 161 | 7 项节点接口测试：INPUT_TYPES/注册/颜色解析 | **需 ComfyUI 环境** |

## 测试运行器

| 文件 | 行数 | 职责 | 分类 |
|------|------|------|------|
| `run_tests.py` | 84 | 一键运行 lib / nodes / integration 测试 | 基础设施 |

## 配方/需求

| 文件 | 职责 |
|------|------|
| `配方.md` | 原始需求说明 + 项目开发规则（14条） |

## 文件分类总览

| 分类 | 包含 | 是否可以随意修改 |
|------|------|----------------|
| 🟥 **核心** | `__init__.py`, `nodes/__init__.py`, `lib/image_utils.py`, `lib/template_engine.py` | ❌ 修改前必须评估影响 |
| 🟧 **业务逻辑** | `nodes/*.py`（除 `__init__.py`） | ✅ 可独立修改 |
| 🟩 **数据** | `templates/*.json` | ✅ 可自由扩展 |
| 🟦 **UI** | `web/xhs_workbench.js` | ✅ 可独立修改 |
| ⬜ **测试** | `tests/*.py`, `run_tests.py` | ✅ 可自由扩展 |