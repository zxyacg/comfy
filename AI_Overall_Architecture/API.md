# API 参考

> **当前状态**：本项目是 ComfyUI 插件，**不提供任何 HTTP API 或 WebSocket 服务**。
> 节点之间通过 ComfyUI 的节点图引擎进行数据传递。

---

## 一、ComfyUI IMAGE 类型接口

这是当前唯一的跨节点数据接口。

### 输入格式

| 属性 | 值 |
|------|-----|
| 类型标识 | `"IMAGE"` |
| Python 类型 | `torch.Tensor` |
| Tensor 形状 | `(B, H, W, C)` |
| 值域 | `[0.0, 1.0]` float32 |
| 通道顺序 | RGB |

### 输出格式

全部 5 个节点都输出 `"IMAGE"` 类型，只有 `XHSImageLoader` 额外输出 `"MASK"` 类型。

| 节点 | 输出类型 |
|------|---------|
| XHSImageLoader | `IMAGE` + `MASK` |
| XHSImageLoaderSimple | `IMAGE` |
| XHSCanvas | `IMAGE` |
| XHSTemplate | `IMAGE` |
| XHSTextOverlay | `IMAGE` |
| XHSExport | `IMAGE` |

---

## 二、节点 INPUT_TYPES 接口

### 2.1 XHSImageLoader

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `image` | 文件选择 | ✅ | 从 ComfyUI input 目录选择图片文件 |
| `target_width` | INT | ❌ | 缩放目标宽度，0=不缩放 |
| `target_height` | INT | ❌ | 缩放目标高度，0=不缩放 |

### 2.2 XHSImageLoaderSimple

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `image` | 文件选择 | ✅ | 从 ComfyUI input 目录选择图片文件 |

### 2.3 XHSCanvas

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `preset` | 下拉选择 | ✅ | 小红书预设尺寸，含"自定义"选项 |
| `width` | INT | ✅ | 自定义宽度，预设选"自定义"时生效 |
| `height` | INT | ✅ | 自定义高度 |
| `background_color` | STRING | ✅ | HEX 颜色值，如 `#FFFFFF` |
| `batch_size` | INT | ✅ | 批量生成数量，1~64 |

### 2.4 XHSTemplate

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `template_name` | 下拉选择 | ✅ | 从 templates/ 目录加载的模板列表 |
| `images` | IMAGE | ✅ | 要填充到模板中的图片 |
| `title_text` | STRING | ✅ | 标题文字（单行） |
| `content_text` | STRING | ✅ | 正文内容（多行） |
| `font_size` | INT | ✅ | 正文字号 |
| `title_size` | INT | ❌ | 标题字号 |

### 2.5 XHSTextOverlay

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `image` | IMAGE | ✅ | 底图 |
| `text` | STRING | ✅ | 要叠加的文字内容（多行） |
| `position_x` | INT | ✅ | 文字左上角 X 坐标 |
| `position_y` | INT | ✅ | 文字左上角 Y 坐标 |
| `font_size` | INT | ✅ | 字号 |
| `color_hex` | STRING | ✅ | 文字颜色 HEX |
| `max_width` | INT | ✅ | 最大宽度，0=不限制 |

### 2.6 XHSExport

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `images` | IMAGE | ✅ | 要导出的图片 |
| `filename_prefix` | STRING | ✅ | 文件名前缀 |
| `format` | 下拉选择 | ✅ | `"png"` / `"jpeg"` |
| `quality` | INT | ✅ | JPEG 质量 10~100 |

---

## 三、Python 库函数接口

### 3.1 `lib/image_utils.py`

```python
tensor_to_pil(image: torch.Tensor) -> Image.Image
pil_to_tensor(image: Image.Image) -> torch.Tensor
resize_image(image: torch.Tensor, width: int, height: int, method: str = "lanczos") -> torch.Tensor
composite_image(background: torch.Tensor, overlay: torch.Tensor, x: int = 0, y: int = 0, mask: torch.Tensor | None = None) -> torch.Tensor
create_blank_canvas(width: int, height: int, color: tuple[int,int,int] = (255,255,255)) -> torch.Tensor
draw_text(image: torch.Tensor, text: str, position: tuple[int,int], font_path: str | None = None, font_size: int = 48, color: tuple[int,int,int] = (0,0,0), max_width: int | None = None, line_spacing: int = 8) -> torch.Tensor
apply_blur(image: torch.Tensor, radius: float = 5.0) -> torch.Tensor
```

### 3.2 `lib/template_engine.py`

```python
# 模板管理
get_templates_dir() -> str
list_templates() -> list[dict]
load_template(template_name: str) -> Template | None

# 模板渲染
render_template(template: Template, images: list[torch.Tensor] | None = None, texts: dict[str, str] | None = None, font_path: str | None = None) -> torch.Tensor

# 数据结构
Template(name, width, height, background_color, zones)
Zone(type, id, x, y, width, height, props)
Template.from_dict(data: dict) -> Template
```

---

## 四、Web UI 扩展接口

**文件**: `web/xhs_workbench.js`

```javascript
// 注册的 ComfyUI 扩展
app.registerExtension({
    name: "XHS.Workbench",
    // 使用 beforeRegisterNodeDef 添加节点样式
    // 使用 loadedGraphNode 添加自定义 UI 组件
})
```

**当前对 ComfyUI 前端 API 的依赖**：
- `app.registerExtension()` — 注册扩展
- `app.canvas` — 操作画布
- `node.addDOMWidget()` — 添加自定义控件（仅在 XHSImageLoader 中使用）
- `node.addWidget()` — 添加标准控件（在 XHSCanvas / XHSExport 中使用）

---

## 五、错误处理

### 节点层错误

| 节点 | 错误场景 | 异常类型 |
|------|---------|---------|
| XHSImageLoader | 无法加载图片文件 | `RuntimeError("无法加载图片: {path}")` |
| XHSTemplate | 找不到模板 | `RuntimeError("找不到模板: {name}")` |

### 工具层错误

工具层函数当前**没有显式错误处理**。输入非法参数时，错误由下方 PIL/Python 直接抛出。

### JSON 加载错误

`load_template()` 和 `list_templates()` 中对 JSON 解析失败静默跳过：

```python
except (json.JSONDecodeError, OSError):
    continue   # 不抛出异常，跳过该文件
```

---

## 六、前后端通信

当前前端（JS）与后端（Python）之间**不直接通信**。
通信完全通过 ComfyUI 节点图引擎进行：

1. 用户在 ComfyUI 工作区中连接节点
2. 前端将节点图数据发送给 ComfyUI 后端
3. ComfyUI 调用节点类的 `FUNCTION` 方法
4. 结果返回前端显示

**不存在任何自定义 HTTP API 或 WebSocket 通道**。