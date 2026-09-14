# 待办事项

> 基于当前代码真实状态整理，不包含不存在的需求。

---

## ✅ 已完成

### 核心功能

- [x] `XHSImageLoader`：加载图片 + 缩放
- [x] `XHSImageLoaderSimple`：简化版图片加载
- [x] `XHSCanvas`：画布创建 + 预设 + HEX 颜色
- [x] `XHSTemplate`：模板渲染（image/text/rect 三种 zone）
- [x] `XHSTextOverlay`：文字叠加 + 中文自动换行
- [x] `XHSExport`：批量导出（PNG/JPEG + 元数据）

### 基础架构

- [x] `lib/image_utils.py`：7 个核心图片处理函数
- [x] `lib/template_engine.py`：模板定义 + 管理 + 渲染
- [x] `templates/classic_card.json` 和 `clean_quote.json`
- [x] `web/xhs_workbench.js`：粉色主题 + 信息显示

### 测试

- [x] `test_lib.py`：19 项工具库测试（独立运行）
- [x] `test_integration.py`：8 项集成测试（独立运行）
- [x] `test_nodes.py`：7 项节点接口测试（需 ComfyUI）
- [x] `run_tests.py`：测试运行器

---

## 🔄 正在进行

| 任务 | 状态 | 说明 |
|------|------|------|
| 完善项目文档 | ✅ 已完成 | AI_Overall_Architecture/ 9 个文档已生成 |

---

## 📋 未完成（按优先级排序）

### P1 — 影响功能完整性

- [ ] **模板文件变更检测**：`XHSTemplate.IS_CHANGED()` 当前仅返回 `template_name`，不会在模板 JSON 文件修改后触发重执行。应比较文件修改时间或内容哈希。
- [ ] **持久化图片预览**：`web/xhs_workbench.js` 中 `XHSImageLoader` 的预览仅为占位，未实现真正的缩略图预览。

### P2 — 技术债务

- [ ] **颜色解析函数统一**：`XHSCanvas._parse_hex_color()` 和 `XHSTextOverlay._parse_hex()` 功能相同，应提取到 `lib/` 中。
- [ ] **tag 文字独立输入**：`XHSTemplate` 中 tag zone 复用 `title_text`，应增加独立的 `tag_text` 输入。
- [ ] **字体路径可配置**：`_DEFAULT_FONT_CANDIDATES` 硬编码系统路径，应支持自定义字体上传或系统字体库扫描。

### P3 — 增强功能

- [ ] **模板预览**：在 `XHSTemplate` 节点中显示模板缩略图预览。
- [ ] **批量文字输入**：支持 CSV/JSON 文件批量输入文字内容。
- [ ] **水印功能**：在 `XHSTextOverlay` 中增加平铺水印选项。
- [ ] **模板编辑器**：可视化模板编辑器，在 Web UI 中创建/修改模板。

---

## 🐛 已知问题

| # | 问题 | 位置 | 影响 | 优先级 |
|---|------|------|------|--------|
| 1 | `XHSTemplate.IS_CHANGED` 不会检测模板文件变化 | `nodes/template.py` | 模板编辑后需重连节点 | P2 |
| 2 | `tag` zone 文本复用 `title_text` | `nodes/template.py` | 无法为 tag 输入独立文字 | P2 |
| 3 | 颜色解析函数重复 | `nodes/canvas.py`, `nodes/text_overlay.py` | 维护成本加倍 | P2 |
| 4 | 字体搜索路径硬编码 | `nodes/text_overlay.py` | 非 Windows 系统可能找不到字体 | P2 |
| 5 | `test_nodes.py` 无法独立运行 | `tests/test_nodes.py` | 需要 ComfyUI 环境，CI 困难 | P3 |
| 6 | 模板文件列表在 `_get_template_names()` 中静态调用 | `nodes/template.py` | `INPUT_TYPES` 在导入时执行，添加模板需重启 ComfyUI | P3 |

---

## 🏗️ 技术债务

| 类别 | 描述 | 位置 | 建议 |
|------|------|------|------|
| 重复代码 | `_parse_hex` / `_parse_hex_color` 重复 | `nodes/canvas.py:95`, `nodes/text_overlay.py:119` | 提取到 `lib/color_utils.py` |
| 硬编码 | 模板路径 | `lib/template_engine.py` 的 `get_templates_dir()` | 支持 ComfyUI 配置或环境变量 |
| 硬编码 | 字体路径 | `nodes/text_overlay.py:17-25` | 扫描系统字体或支持自定义上传 |
| 性能 | `_wrap_text` 使用正则逐 token 分词 | `lib/image_utils.py:166` | 对长文本可能较慢，可缓存或优化 |
| 测试 | 节点测试依赖 ComfyUI 环境 | `tests/test_nodes.py` | 考虑 mock ComfyUI 模块 |
| 配置 | 无独立配置文件 | 全部 | 考虑引入 `config.py` |