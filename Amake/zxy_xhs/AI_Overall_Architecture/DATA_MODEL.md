# 数据模型

> 以下数据模型全部基于当前代码库中的真实定义。
> 标记含义：🔒 稳定的（不建议修改）、🔧 可修改的、⚠️ 需要谨慎修改的

---

## 一、Python Dataclass

### 1.1 Zone — 模板区域 🔒

**定义位置**: `lib/template_engine.py`

```python
@dataclass
class Zone:
    type: str                    # "image" / "text" / "rect"
    id: str = ""                 # 区域标识（用于文字匹配）
    x: int = 0
    y: int = 0
    width: int = 0
    height: int = 0
    props: dict[str, Any] = field(default_factory=dict)
```

**字段说明**：

| 字段 | 类型 | 说明 | 稳定度 |
|------|------|------|--------|
| `type` | str | 区域类型，决定渲染方式 | 🔒 |
| `id` | str | 匹配 `texts` 字典的 key | 🔒（修改会影响 JSON 模板和 template.py 匹配逻辑） |
| `x`, `y` | int | 左上角坐标 | 🔒 |
| `width`, `height` | int | 区域尺寸 | 🔒 |
| `props` | dict | 额外属性，存 font_size/color 等 | 🔧（可扩展） |

**`props` 字典支持的键**（取决于 `type`）：

| type | props 键 | 类型 | 说明 |
|------|---------|------|------|
| `image` | `fit` | str | `"cover"` / `"contain"` / `"fill"` |
| `text` | `font_size` | int | 字号 |
| `text` | `color` | list[int] | [R, G, B] |
| `text` | `align` | str | `"left"` / `"center"` / `"right"` |
| `text` | `max_lines` | int | 最大行数 |
| `rect` | `color` | list[int] | [R, G, B] 填充色 |

### 1.2 Template — 模板定义 🔒

**定义位置**: `lib/template_engine.py`

```python
@dataclass
class Template:
    name: str
    width: int
    height: int
    background_color: tuple[int, int, int] = (255, 255, 255)
    zones: list[Zone] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict) -> "Template": ...
```

**字段说明**：

| 字段 | 类型 | 说明 | 稳定度 |
|------|------|------|--------|
| `name` | str | 模板名称 | 🔒 |
| `width` | int | 画布宽度 | 🔒 |
| `height` | int | 画布高度 | 🔒 |
| `background_color` | tuple | 背景色 RGB | 🔒 |
| `zones` | list[Zone] | 区域列表 | 🔒 |

---

## 二、JSON 模板数据结构

### 2.1 模板 JSON 格式

**数据位置**: `templates/*.json`

```json
{
    "name": "模板名称",
    "width": 1080,
    "height": 1440,
    "background_color": [255, 255, 255],
    "zones": [
        {
            "id": "main_image",
            "type": "image",
            "x": 0, "y": 0,
            "width": 1080, "height": 1080,
            "fit": "cover"
        },
        {
            "id": "content",
            "type": "text",
            "x": 60, "y": 1120,
            "width": 960, "height": 200,
            "font_size": 48,
            "color": [51, 51, 51],
            "align": "left",
            "max_lines": 3
        },
        {
            "id": "bottom_bg",
            "type": "rect",
            "x": 0, "y": 1080,
            "width": 1080, "height": 360,
            "color": [248, 248, 248]
        }
    ]
}
```

**JSON 与 dataclass 映射关系**：

| JSON 字段 | Dataclass 字段 | 处理逻辑 |
|-----------|---------------|---------|
| `type` | `type` | 直接映射 |
| `id` | `id` | 直接映射 |
| `x`, `y`, `width`, `height` | 同名 | 直接映射 |
| 除上述 6 个字段外所有键 | `props` 字典 | `from_dict()` 中自动提取 |

**关键约束**：
- zone 的 `id` 必须与 XHSTemplate 节点中的匹配逻辑一致（参考下文"节点文字匹配逻辑"）
- JSON 中的颜色值为 `[R, G, B]` 格式（0-255），代码中会转换为 tuple

### 2.2 现有模板

| 文件 | name | 尺寸 | 特点 |
|------|------|------|------|
| `classic_card.json` | "经典卡片" | 1080×1440 | 上图片 + 底部灰底 + 标题 + 正文 |
| `clean_quote.json` | "简约语录" | 1080×1440 | 上图片（有边距）+ 白底 + 内容 + 标签 |

---

## 三、节点文字匹配逻辑 🔒

**定义位置**: `nodes/template.py` 的 `apply_template()` 方法

```python
texts = {}
for zone in template.zones:
    if zone.type == "text":
        if zone.id == "title" and title_text:
            texts[zone.id] = title_text
        elif zone.id == "content" and content_text:
            texts[zone.id] = content_text
        elif zone.id == "tag" and title_text:
            texts[zone.id] = title_text
```

**匹配规则**：

| zone.id | 来源 | 说明 |
|---------|------|------|
| `"title"` | `title_text` 输入 | 标题文字 |
| `"content"` | `content_text` 输入 | 正文内容 |
| `"tag"` | `title_text` 输入（回退） | 标签文字，当前复用标题 |

> ⚠️ **注意**：`tag` 当前复用 `title_text` 而非独立输入。如果需要独立的标签输入，需要修改 `XHSTemplate.INPUT_TYPES` 并更新匹配逻辑。

---

## 四、ComfyUI IMAGE Tensor

这是 ComfyUI 系统中所有节点之间传递图片的标准格式：

```
形状: (B, H, W, C)
  B = batch_size（图片张数）
  H = height（像素）
  W = width（像素）
  C = 3（RGB 通道）

值域: [0.0, 1.0], float32
通道顺序: RGB
```

**转换函数**（在 `lib/image_utils.py` 中）：

| 函数 | 方向 | 说明 |
|------|------|------|
| `tensor_to_pil(tensor)` | Tensor → PIL | B=1 时自动 squeeze |
| `pil_to_tensor(pil)` | PIL → Tensor | 加入 batch 维度 |

---

## 五、其他数据结构

### 5.1 模板元信息（list_templates 返回值）

```python
# 返回类型: list[dict]
[
    {
        "file": "classic_card.json",   # 文件名
        "name": "经典卡片",             # 模板名称
        "width": 1080,                 # 宽度
        "height": 1440,                # 高度
    },
    ...
]
```

### 5.2 导出结果（XHSExport 的 UI 输出）

```python
# 返回类型: dict 包含 "ui"
{
    "ui": {
        "images": [
            {
                "filename": "XHS_00001.png",
                "subfolder": "",
                "type": "output",
            },
            ...
        ]
    },
    "result": (images_tensor,)
}
```

### 5.3 XHSCanvas 预设

```python
XHS_PRESETS = {
    "竖版 3:4 (1080x1440)": (1080, 1440),
    "竖版 3:4 (1242x1660)": (1242, 1660),
    "方形 1:1 (1080x1080)": (1080, 1080),
    "横版 4:3 (1440x1080)": (1440, 1080),
    "横版 16:9 (1920x1080)": (1920, 1080),
    "自定义": (0, 0),
}
```

### 5.4 文本颜色解析

```python
# HEX → RGB tuple，支持 #RRGGBB 和 #RGB 格式
# 默认值：白色 (255, 255, 255)
# 定义在：nodes/canvas.py 和 nodes/text_overlay.py（各自独立实现）
_parse_hex_color("#FF6B81")  # → (255, 107, 129)
_parse_hex_color("#FFF")     # → (255, 255, 255)
```

> ⚠️ **注意**：`XHSCanvas._parse_hex_color()` 和 `XHSTextOverlay._parse_hex()` 是各自独立实现的静态方法，功能相同但命名不同。这是一个轻微的技术债务。

---

## 六、数据结构稳定性总览

| 数据结构 | 位置 | 稳定度 | 说明 |
|---------|------|--------|------|
| `Zone` dataclass | `lib/template_engine.py` | 🔒 稳定 | 修改破坏 JSON 模板兼容性 |
| `Template` dataclass | `lib/template_engine.py` | 🔒 稳定 | 同上 |
| JSON 模板格式 | `templates/*.json` | 🔒 稳定 | 与 Zone/Template 绑定 |
| IMAGE tensor 格式 | 整个 ComfyUI | 🔒 外部约定 | 不可修改 |
| `XHS_PRESETS` | `nodes/canvas.py` | 🔧 可扩展 | 可添加新预设 |
| `_DEFAULT_FONT_CANDIDATES` | `nodes/text_overlay.py` | 🔧 可扩展 | 可添加字体路径 |
| 节点文字匹配逻辑 | `nodes/template.py` | ⚠️ 需谨慎 | 修改影响所有模板渲染 |
| 颜色解析函数 | `nodes/canvas.py` / `nodes/text_overlay.py` | 🔧 可重构 | 重复代码，可提取到 lib |