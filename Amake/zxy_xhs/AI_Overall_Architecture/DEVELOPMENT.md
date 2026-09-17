# 开发指南

> 本文档记录本项目的开发规则和约定，面向参与本项目的 AI 开发者。
> 规则来源：`配方.md` 的"项目开发规则" + 代码实际结构。

## 一、核心规则

### 规则 1：每个文件不超过 300 行

当前状态：✅ **全部合规**

| 文件 | 行数 |
|------|------|
| `lib/template_engine.py` | 211 ← 最大 |
| `lib/image_utils.py` | 196 |
| `tests/test_lib.py` | 196 |
| `tests/test_integration.py` | 162 |
| `tests/test_nodes.py` | 161 |
| `nodes/image_loader.py` | 151 |
| `nodes/exporter.py` | 124 |
| `nodes/template.py` | 121 |
| `nodes/text_overlay.py` | 127 |
| `nodes/canvas.py` | 102 |
| 其余 | < 90 |

不能为了凑 300 行而机械拆分文件。

### 规则 2：新功能优先新增模块

- 如果新功能需要新的节点 → 在 `nodes/` 下新建文件
- 如果新功能需要新的工具函数 → 在 `lib/` 下新建文件或在已有文件中新增函数
- ❌ 禁止为加一个功能同时修改 3 个以上无关模块

### 规则 3：不允许顺手重构

- 一个功能对应一次改动
- 如果发现现有代码可以优化 → 记录到 TODO.md，不要混在当前改动中
- ✅ 正确做法："修复 A 的 bug" → commit → "重构 B 的结构" → commit

### 规则 4：修改公共接口前必须说明影响范围

公共接口包括：
- `lib/image_utils.py` 中任何导出函数
- `lib/template_engine.py` 中 `Zone`、`Template` 数据结构
- `lib/template_engine.py` 中 `render_template()`、`load_template()`、`list_templates()`
- `nodes/__init__.py` 中的节点映射
- 任何节点的 `INPUT_TYPES` 返回值结构

修改上述内容前，必须在修改说明中列出所有受影响的调用方。

### 规则 5：前端不能直接访问文件系统

- `web/` 下的 JS 仅能操作 DOM 和调用 ComfyUI 前端 API
- ❌ 禁止使用 `fetch()` 访问 `file://` 协议
- ❌ 禁止引入 Node.js 的 `fs` 模块

### 规则 6：业务模块不能直接依赖 ComfyUI 内部实现

- `lib/` 目录下的代码禁止 import `folder_paths`、`node_helpers` 等 ComfyUI 内部模块
- 只有 `nodes/` 同一层级的代码可以依赖 ComfyUI
- 如果需要在 lib 中使用 ComfyUI 的功能 → 通过参数注入或回调函数

### 规则 7：模块之间通过接口通信

```
正确:
  nodes/template.py  →  import ..lib.template_engine  (公共函数)
  lib/template_engine.py  →  import ..lib.image_utils  (公共函数)

错误:
  nodes/canvas.py  →  import ..nodes.template  (节点间互调)
  lib/template_engine.py  →  import ..nodes.canvas  (工具层反调节点层)
```

### 规则 8：禁止复制粘贴大量重复业务逻辑

如果发现两个节点有相似的图片处理逻辑 → 提取公共函数到 `lib/`

当前已知重复：
- `nodes/image_loader.py` 和 `nodes/exporter.py` 都有 tensor→PIL 转换（但用法不同，当前不视为重复）

### 规则 9：不确定架构时先分析

如果对某个改动的影响范围不确定：
1. 先阅读 ARCHITECTURE.md
2. 搜索代码中所有调用目标函数的地方
3. 列出所有受影响文件
4. 确认后开始修改

### 规则 10：每完成独立功能必须 Git commit

建议的 commit 粒度：
- 一个新节点 + 其注册 + 对应测试
- 一个新工具函数 + 对应测试
- 一个 bug 修复 + 对应测试
- 一个配置/文档变更

### 规则 11：修改前必须阅读相关模块

修改 `nodes/canvas.py` 前阅读：
1. `lib/image_utils.py`（了解 create_blank_canvas 的实现）
2. `tests/test_lib.py` 相关测试
3. `tests/test_nodes.py` 中 XHSCanvas 的测试

### 规则 12：修改完成必须运行相关测试

| 修改范围 | 必须运行的测试 |
|---------|--------------|
| `lib/*` | `python run_tests.py lib` |
| `nodes/*` | `python run_tests.py nodes`（需 ComfyUI） + `python run_tests.py integration` |
| `templates/*` | `python run_tests.py lib` |
| `web/*` | 手动在浏览器/ComfyUI 前端验证 |

## 二、分支策略

当前项目在 `Amake/zxy_xhs/` 目录下，是 ComfyUI 仓库的一部分。
建议保持单分支开发，每个独立功能提交一次。

## 三、测试约定

- `test_lib.py`：测试 `lib/` 下的纯函数，不依赖 ComfyUI
- `test_integration.py`：测试多模块组合工作流，不依赖 ComfyUI
- `test_nodes.py`：测试节点接口定义，**需要 ComfyUI 环境**
- 所有测试使用 Python 标准库 `unittest`
- 测试文件命名：`test_<模块名>.py`
- 测试类命名：`Test<功能>`（如 `TestImageUtils`）
- 测试方法命名：`test_<场景>`（如 `test_create_blank_canvas_shape`）

## 四、命名规范

| 类型 | 规范 | 示例 |
|------|------|------|
| 节点类 | XHS + 功能名 (PascalCase) | `XHSCanvas`, `XHSTemplate` |
| 节点文件 | 功能名小写 | `canvas.py`, `exporter.py` |
| 工具函数 | 动词 + 名词 (snake_case) | `create_blank_canvas`, `draw_text` |
| 模板文件 | 英文 + `.json` | `classic_card.json` |
| 测试文件 | `test_` + 模块名 | `test_lib.py` |

## 五、ComfyUI 节点开发约定

### 节点必需属性

```python
class XHSExample:
    @classmethod
    def INPUT_TYPES(cls) -> dict:
        return {"required": {...}, "optional": {...}}

    RETURN_TYPES = ("IMAGE",)            # ComfyUI 类型
    RETURN_NAMES = ("image",)            # 输出名称
    FUNCTION = "process"                 # 入口方法名
    CATEGORY = "XHS Tools"              # 统一前缀
    DESCRIPTION = "..."                  # 描述
```

### 节点命名约束

- CATEGORY 必须以 `XHS` 开头（当前使用 `"XHS Tools"`）
- 节点注册键名使用 camelCase（如 `"XHSCanvas"`）
- 显示名称使用自然语言（如 `"XHS Canvas"`）