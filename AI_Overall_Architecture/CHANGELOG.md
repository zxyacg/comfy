# 变更日志

> **重要说明**：本项目在 `Amake/zxy_xhs/` 目录下开发，属于 ComfyUI 仓库的子目录。
> 当前在该目录下**无独立 Git 历史记录**。以下日志根据代码内容和对话历史整理。

---

## v1.0.0 — 第一版（当前版本）

### 架构

- 采用三层架构：`lib/`（工具层）→ `nodes/`（节点层）→ `web/`（UI 层）
- `lib/` 完全独立于 ComfyUI 运行时，可单独测试
- 节点彼此独立，不互相依赖，通过 ComfyUI 节点图引擎通信

### 已完成功能

#### 节点（5 + 1）

- [X] **XHSImageLoader** — 从 ComfyUI input 目录加载图片，支持批量、缩放
- [X] **XHSImageLoaderSimple** — 简化版图片加载，无缩放选项
- [X] **XHSCanvas** — 创建空白画布，支持 5 种预设 + 自定义，HEX 颜色
- [X] **XHSTemplate** — 模板渲染，从 JSON 模板读取布局，自动匹配文字到 zone id
- [X] **XHSTextOverlay** — 文字叠加，支持中文自动换行、HEX 颜色
- [X] **XHSExport** — 批量导出到 output 目录，PNG/JPEG + 元数据

#### 模板

- [X] "经典卡片"模板（classic_card.json）：上图片 + 下灰底 + 标题 + 正文
- [X] "简约语录"模板（clean_quote.json）：上图 + 下白底 + 内容 + 标签

#### 工具库

- [X] 图片工具（`lib/image_utils.py`）：tensor↔PIL、缩放、合成、画布、文字、模糊
- [X] 模板引擎（`lib/template_engine.py`）：Template/Zone 数据结构、加载、渲染

#### 前端

- [X] XHS 节点粉色主题
- [X] 图片预览占位（XHSImageLoader）
- [X] 画布尺寸信息显示（XHSCanvas）

#### 测试

- [X] 工具库单元测试（19 项）
- [X] 集成测试（8 项）
- [X] 节点接口测试（7 项，需 ComfyUI 环境）
- [X] 测试运行器

### 已知问题

- `nodes/exporter.py` 和 `nodes/image_loader.py` 直接依赖 `folder_paths`，这是 `nodes/` 层的合规依赖
- `XHSTextOverlay` 的 `_parse_hex()` 和 `XHSCanvas` 的 `_parse_hex_color()` 是重复的静态方法
- `XHSTemplate` 的 `IS_CHANGED` 方法仅返回 `template_name`，不支持检测模板文件内容变化
- `XHSTemplate` 中 `tag` zone 的文本当前复用 `title_text`，无独立输入
- 字体搜索路径硬编码了 Windows/macOS/Linux 路径

### 技术债务

- 颜色解析函数在两个节点中各自独立实现
- `_wrap_text()` 使用了正则分词，性能可能不如专用文本编排库
- 无路径配置化，模板目录默认硬编码在 `get_templates_dir()`