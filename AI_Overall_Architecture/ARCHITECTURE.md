# 系统架构

## 一、整体架构

```
┌─────────────────────────────────────────────────────────┐
│                    ComfyUI 主进程                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │              custom_nodes / 插件层                │   │
│  │  ┌───────────────────────────────────────────┐   │   │
│  │  │         XHS Workflow Nodes 插件            │   │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌────────┐  │   │   │
│  │  │  │ 节点层    │  │ 工具层   │  │ 前端UI │  │   │   │
│  │  │  │ (nodes/) │─▶│ (lib/)   │  │ (web/) │  │   │   │
│  │  │  └──────────┘  └──────────┘  └────────┘  │   │   │
│  │  │  ┌──────────┐  ┌──────────┐              │   │   │
│  │  │  │ 模板数据  │  │ 测试套件  │              │   │   │
│  │  │  │(templats/)│  │ (tests/) │              │   │   │
│  │  │  └──────────┘  └──────────┘              │   │   │
│  │  └───────────────────────────────────────────┘   │   │
│  └──────────────────────────────────────────────────┘   │
│                                                         │
│  ┌──────────────────────────────────────────────────┐   │
│  │              ComfyUI 内部模块                      │   │
│  │  folder_paths  /  node_helpers  /  内部节点引擎   │   │
│  └──────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### 各层职责

| 层 | 目录 | 职责 | 是否可以依赖 ComfyUI |
|----|------|------|---------------------|
| **节点层** | `nodes/` | ComfyUI 节点定义，连接 UI 和工具层 | ✅ 可以 |
| **工具层** | `lib/` | 核心业务逻辑，纯 Python 实现 | ❌ 禁止 |
| **前端 UI** | `web/` | 节点外观、交互增强（JS） | ❌ 不能直接访问文件系统 |
| **模板数据** | `templates/` | JSON 格式模板定义 | — |
| **测试套件** | `tests/` | 单元测试 + 集成测试 | 部分依赖 |

## 二、模块依赖关系

### 允许的依赖方向

```
web/ ───→ ComfyUI 前端 API (app.js 等)
  │
  │ (仅 DOM 操作，不调 Node.js API)
  ▼
nodes/ ──→ lib/       (通过 import ..lib.xxx)
nodes/ ──→ folder_paths (ComfyUI 内部)
nodes/ ──→ node_helpers  (ComfyUI 内部)
  │
  ▼
lib/ ───→ torch / PIL / numpy  (纯 Python 第三方)
lib/ ──→ templates/  (通过 get_templates_dir() 读 JSON)
  │
  ▼
templates/  (JSON 数据，无代码)
tests/ ──→ lib/       (独立测试)
tests/ ──→ nodes/     (需 ComfyUI 环境)
```

### 禁止的依赖方向

| 禁止的依赖 | 原因 |
|-----------|------|
| `lib/` → `nodes/` | 工具层不能依赖节点层 |
| `lib/` → `web/` | 工具层不能依赖前端 |
| `lib/` → `folder_paths` | 工具层应独立于 ComfyUI 运行时 |
| `lib/` → `node_helpers` | 同上 |
| `web/` → 文件系统 | 前端不能直接操作文件 |
| `web/` → `lib/` | 前端不能导入 Python 模块 |
| `nodes/` → `web/` | 节点层不依赖前端 |
| `nodes/` ↔ `nodes/` (交叉依赖) | 节点间不应互相 import |

### 当前实际依赖（已验证代码）

| 源文件 | 依赖了哪些外部模块 |
|--------|------------------|
| `nodes/image_loader.py` | `torch`, `folder_paths`, `node_helpers`, `PIL`, `numpy` |
| `nodes/canvas.py` | `torch`, `..lib.image_utils` |
| `nodes/template.py` | `torch`, `..lib.template_engine` |
| `nodes/text_overlay.py` | `torch`, `..lib.image_utils` |
| `nodes/exporter.py` | `torch`, `folder_paths`, `PIL`, `numpy`, `json`, `os` |
| `lib/image_utils.py` | `torch`, `PIL`, `numpy`, `re` |
| `lib/template_engine.py` | `torch`, `..lib.image_utils`, `json`, `os` |
| `web/xhs_workbench.js` | `../../scripts/app.js` (ComfyUI 前端 API) |

## 三、核心模块说明

### 3.1 工具层 (`lib/`) — 基础设施

**不可随意修改**。所有节点依赖此层的函数。

| 文件 | 职责 | 行数 | 稳定性 |
|------|------|------|--------|
| `image_utils.py` | 图片加载、缩放、合成、绘图 | 196 | ⚠️ 稳定，修改会影响所有节点 |
| `template_engine.py` | 模板定义、管理、渲染 | 211 | ⚠️ 稳定，Zone/Template 数据结构修改会影响模板 JSON |

### 3.2 节点层 (`nodes/`) — 业务逻辑

每个节点独立，不互相依赖。

| 文件 | 职责 | 行数 | 修改影响范围 |
|------|------|------|------------|
| `image_loader.py` | 图片加载节点 + 简化版加载节点 | 151 | 仅自身 |
| `canvas.py` | 画布创建节点 | 102 | 仅自身 |
| `template.py` | 模板渲染节点 | 121 | 仅自身 |
| `text_overlay.py` | 文字叠加节点 | 127 | 仅自身 |
| `exporter.py` | 批量导出节点 | 124 | 仅自身 |

### 3.3 前端 (`web/`) — UI 增强

| 文件 | 职责 | 行数 |
|------|------|------|
| `xhs_workbench.js` | 节点颜色主题、交互增强 | 78 |

## 四、数据流

### 4.1 完整工作流

```
XHS Image Loader ──→ XHS Canvas ──→ XHS Template ──→ XHS Text Overlay ──→ XHS Export
       │                  │               │                  │                  │
       ▼                  ▼               ▼                  ▼                  ▼
   (IMAGE tensor)   (IMAGE tensor)   (IMAGE tensor)    (IMAGE tensor)       (文件 + IMAGE)
```

### 4.2 数据类型流

```
图片文件 (jpg/png)
    │
    ▼
XHSImageLoader ──→ torch.Tensor (B, H, W, 3)  ──→ "IMAGE" 类型
XHSCanvas      ──→ torch.Tensor (B, H, W, 3)  ──→ "IMAGE" 类型
XHSTemplate    ──→ torch.Tensor (B, H, W, 3)  ──→ "IMAGE" 类型
XHSTextOverlay ──→ torch.Tensor (B, H, W, 3)  ──→ "IMAGE" 类型
XHSExport      ──→ 文件 + torch.Tensor (B, H, W, 3)
```

### 4.3 模板渲染数据流

```
JSON 模板文件 (templates/*.json)
    │
    ▼
list_templates() / load_template() ──→ Template & Zone dataclasses
    │
    ▼
render_template() ──→ 遍历 zones
    │    ├── type="image"  → resize_image() + composite_image()
    │    ├── type="text"   → draw_text()
    │    └── type="rect"   → create_blank_canvas() + composite_image()
    │
    ▼
最終 IMAGE tensor
```

## 五、修改影响范围指南

| 如果你修改了... | 可能受影响的是... |
|---------------|-----------------|
| `lib/image_utils.py` 的函数签名 | `nodes/canvas.py`, `nodes/text_overlay.py`, `lib/template_engine.py` |
| `lib/image_utils.py` 的实现逻辑 | 调用方无影响（行为变化） |
| `lib/template_engine.py` 的 Zone/Template 数据结构 | `nodes/template.py`, `templates/*.json` 格式 |
| `lib/template_engine.py` 的渲染逻辑 | 仅 `nodes/template.py` |
| `nodes/__init__.py` 的节点注册 | 所有调用方需知道映射变化 |
| `nodes/` 下某个节点的 INPUT_TYPES | 该节点的工作流配置 |
| `templates/*.json` 的 zone id | `nodes/template.py` 的文字匹配逻辑 |
| `web/xhs_workbench.js` | 仅前端外观 |

## 六、未在代码中体现的架构约束（配方.md 要求）

| 约束 | 当前状态 |
|------|---------|
| 前端不能直接操作文件系统 | ✅ 当前 JS 无文件操作 |
| 业务模块不能直接依赖 ComfyUI 内部实现 | ⚠️ `nodes/exporter.py` 直接依赖 `folder_paths`，这是节点层，合规 |
| 所有业务逻辑必须经过 Service 接口 | ❌ 当前无 Service 层，`lib/` 充当此角色 |
| 数据结构必须定义在 types/models 中 | ❌ 当前在 `lib/template_engine.py` 中以 dataclass 定义 |