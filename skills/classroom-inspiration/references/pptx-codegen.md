# PPT 代码生成指南

> **加载条件**：进入 Phase 3.13（代码生成阶段），或用户明确要求生成可运行的 PPT 代码时加载。
> **预计加载量**：约 350 行

---

## 3.13 python-pptx 代码生成

### 代码生成核心规则

1. **始终先输出完整 Python 脚本文件**，再解释核心步骤
2. **使用 python-pptx 库**（官方文档：python-pptx.readthedocs.io）
3. **Output 文件路径规则**：生成 `output/` 目录，文件名 = `{课题}_{学科}_{日期}.pptx`
4. 日期格式：YYYYMMDD
5. 确保脚本可直接运行（含必要的 import、main() 入口）

### 运行前准备

- `pip install python-pptx`
- 字体相关：Win/Mac 字体路径不同，需根据平台适配
- 图片资源：使用占位符路径或随机占位图 API（picsum.photos）

### 常见字体路径

```python
# Windows 字体路径
FONT_PATH = "C:/Windows/Fonts/"

# macOS 字体路径
FONT_PATH = "/System/Library/Fonts/"

# 常用备选
font_names = {
    "title": "微软雅黑" if is_windows else "PingFang SC",
    "body": "微软雅黑" if is_windows else "PingFang SC",
    "english": "Arial" if is_windows else "Helvetica",
}
```

### 代码生成模板

#### 基础框架

```python
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE
import datetime

# --- 配置参数 ---
SUBJECT = "学科"
TOPIC = "课题"
TEACHER = "教师姓名"
GRADE = "年级"
COLOR_PRIMARY = RGBColor(0x2D, 0x5A, 0x27)   # 主色
COLOR_SECONDARY = RGBColor(0xF5, 0xF0, 0xE8) # 辅色
COLOR_ACCENT = RGBColor(0xC2, 0x3B, 0x22)    # 强调色

prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

today = datetime.date.today().strftime("%Y%m%d")
output_path = f"output/{TOPIC}_{SUBJECT}_{today}.pptx"
```

#### 辅助函数库

```python
def add_textbox(slide, left, top, width, height, text, font_size=18,
                font_name=None, bold=False, color=RGBColor(0,0,0),
                alignment=PP_ALIGN.LEFT):
    """添加文本框的通用函数"""
    txBox = slide.shapes.add_textbox(Inches(left), Inches(top),
                                      Inches(width), Inches(height))
    tf = txBox.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    if font_name:
        p.font.name = font_name
    p.font.bold = bold
    p.font.color.rgb = color
    p.alignment = alignment
    return txBox

def add_shape_with_text(slide, left, top, width, height, text, shape_type=MSO_SHAPE.ROUNDED_RECTANGLE,
                        fill_color=RGBColor(0xE8, 0xE8, 0xE8), font_size=14,
                        font_color=RGBColor(0,0,0)):
    """添加带填充色的形状+文字"""
    shape = slide.shapes.add_shape(shape_type, Inches(left), Inches(top),
                                    Inches(width), Inches(height))
    shape.fill.solid()
    shape.fill.fore_color.rgb = fill_color
    shape.line.fill.background()
    tf = shape.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(font_size)
    p.font.color.rgb = font_color
    p.alignment = PP_ALIGN.CENTER
    return shape
```

### 页面生成规格

#### 封面页 A

```python
def create_cover(prs, subject, topic, teacher, grade):
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # 空白布局
    # 背景色填充
    background = slide.background
    fill = background.fill
    fill.solid()
    fill.fore_color.rgb = COLOR_PRIMARY
    
    # 标题（居中对齐）
    add_textbox(slide, 1, 2.5, 11.333, 2, topic,
                font_size=44, bold=True, color=COLOR_SECONDARY,
                alignment=PP_ALIGN.CENTER)
    # 副标题行
    add_textbox(slide, 1, 5, 11.333, 1, f"{subject} · {grade}  |  {teacher}",
                font_size=18, color=COLOR_SECONDARY, alignment=PP_ALIGN.CENTER)
    return slide
```

#### 其他页面（快速参考）

| 页面类型 | 创建函数 | 关键元素 | 配色 |
|---------|---------|---------|------|
| 封面 A | `create_cover()` | 标题 + 副标题 | 主色背景 |
| 导入 B | `create_intro()` | 左侧图片占位 + 右侧问题 | 辅色背景 |
| 目标 C | `create_objectives()` | 三栏卡片 | 白色背景 + 色块区分 |
| 知识 D | `create_knowledge()` | 图文混排 | 按层级递进上色 |
| 活动 E | `create_activity()` | 步骤框 + 计时器 | 强调色点缀 |
| 总结 F | `create_summary()` | 知识地图 + 分层作业 | 全色系汇总 |

各函数签名：

```python
def create_intro(prs, question, image_path="", keywords=[]): ...
def create_objectives(prs, objectives_by_level): ...
def create_knowledge(prs, layers): ...
def create_activity(prs, name, steps, duration): ...
def create_summary(prs, concept_map, homework_levels): ...
```

### 完整脚本模板

```python
def main():
    # 1. 初始化
    # 2. 创建各页面（按顺序）
    # 3. 保存
    prs.save(output_path)
    print(f"✅ PPT 已生成: {output_path}")

if __name__ == "__main__":
    main()
```

### Slide Master 编号参考

```python
# prs.slide_layouts[0] — 标题幻灯片
# prs.slide_layouts[1] — 标题和内容
# prs.slide_layouts[2] — 节标题
# prs.slide_layouts[3] — 两栏内容
# prs.slide_layouts[4] — 空白（有占位符）
# prs.slide_layouts[5] — 标题和竖排文字
# prs.slide_layouts[6] — 完全空白（推荐）
```

### 典型布局尺寸（宽屏 16:9）

| 区域 | 位置 (inches) | 尺寸 |
|------|-------------|------|
| 标题栏 | top=0.5 | height=1.0 |
| 正文区 | top=1.5 | height=5.0 |
| 底部栏 | top=6.5 | height=0.8 |
| 左侧边距 | left=0.5 | width=12.333 |
| 三栏左 | left=0.5 | width=3.7 |
| 三栏中 | left=4.8 | width=3.7 |
| 三栏右 | left=9.1 | width=3.7 |

---

## 3.14 视觉升级代码（扩展）

### 渐变色背景（替代纯色）

```python
# python-pptx 不支持渐变直接设置，用形状覆盖实现：
def add_gradient_bg(slide, color_top, color_bottom):
    """用两个矩形模拟渐变背景"""
    from pptx.util import Inches
    # 上半部分
    shape1 = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(0),
        Inches(13.333), Inches(3.75))
    shape1.fill.solid()
    shape1.fill.fore_color.rgb = color_top
    shape1.line.fill.background()
    # 下半部分
    shape2 = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE, Inches(0), Inches(3.75),
        Inches(13.333), Inches(3.75))
    shape2.fill.solid()
    shape2.fill.fore_color.rgb = color_bottom
    shape2.line.fill.background()
```

### 时间线进度条

```python
def add_timeline(slide, current_section, total_sections):
    """在底部添加进度条"""
    bar_width = 12.333
    section_width = bar_width / total_sections
    for i in range(total_sections):
        x = 0.5 + i * section_width
        color = COLOR_ACCENT if i < current_section else RGBColor(0xE0, 0xE0, 0xE0)
        shape = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(x), Inches(7.0),
            Inches(section_width - 0.1), Inches(0.15))
        shape.fill.solid()
        shape.fill.fore_color.rgb = color
        shape.line.fill.background()
```

### 图表集成

```python
# 用 add_shape + text 模拟柱状图
def add_bar_chart(slide, data, left, top, width, height):
    """data: [(label, value, color), ...], value 0-100"""
    max_val = max(v for _, v, _ in data)
    bar_count = len(data)
    bar_width = width / (bar_count * 2)
    
    for i, (label, value, color) in enumerate(data):
        bar_h = (value / max_val) * height
        x = left + i * (bar_width * 2) + bar_width / 2
        y = top + height - bar_h
        bar = slide.shapes.add_shape(
            MSO_SHAPE.RECTANGLE, Inches(x), Inches(y),
            Inches(bar_width), Inches(bar_h))
        bar.fill.solid()
        bar.fill.fore_color.rgb = color
        bar.line.fill.background()
```

---

## 3.16 故事化叙事结构

### 三幕式叙事结构

```
第一幕（建立）→ 第二幕（对抗）→ 第三幕（解决）

第一幕：建立情境
  - 问题：你知道__吗？
  - 冲突：但__不是表面那么简单
  - 驱动：让我们一起来揭开__的秘密

第二幕：探索过程
  - 尝试：如果是你，你会怎么做？→ 活动1
  - 发现：通过活动1我们发现__ → 还缺什么？
  - 深入：那如果再加入__会怎样？→ 活动2
  - 突破：终于发现__的规律！

第三幕：应用升华
  - 应用：现在用这个规律来解决一个问题
  - 反思：回顾今天的学习旅程，你最大的收获是？
  - 延伸：这个问题在真实世界中还出现在哪里？
```

### 叙事节奏格

| 时间点 | 叙事要素 | 情感曲线 |
|--------|---------|---------|
| 0-3min | 导入惊喜/认知冲突 | ↗ 上升 |
| 3-8min | 基础概念建立 | → 平稳 |
| 8-15min | 第一次挑战/活动 | ↗↘ 小高潮 |
| 15-25min | 深入探究 | → 平稳 |
| 25-35min | 创造力释放/展示 | ↗ 大高潮 |
| 35-40min | 总结升华/情感共鸣 | ↘ 温暖收尾 |

### 故事化过渡句

- "经过刚才的探索，我们拿到了第一把'钥匙'——但真正的宝藏还在后面。"
- "现在暂停一下，想想看——如果故事在这里结束，你会满意吗？不会，因为最精彩的部分才刚刚开始。"
- "这是爱因斯坦小时候也问过的问题——他用了十年才找到答案，而今天，你们只用一节课。"

---

## 课后分层作业模板（代码生成）

```python
def create_homework_slide(prs, basic, challenge, creative):
    """基础/挑战/创意三层作业"""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    # 标题
    add_textbox(slide, 0.5, 0.3, 12, 0.8, "📋 课后探索任务",
                font_size=32, bold=True, color=COLOR_PRIMARY,
                alignment=PP_ALIGN.CENTER)
    columns = [
        ("⭐ 基础任务", basic, COLOR_PRIMARY),
        ("🚀 挑战任务", challenge, COLOR_ACCENT),
        ("🎨 创意任务", creative, RGBColor(0x7B, 0x1F, 0xA2)),
    ]
    for i, (title, content, color) in enumerate(columns):
        x = 0.5 + i * 4.2
        add_shape_with_text(slide, x, 1.5, 3.8, 0.6, title,
                            fill_color=color, font_size=18, font_color=RGBColor(0xFF,0xFF,0xFF))
        add_textbox(slide, x, 2.3, 3.8, 4, content, font_size=14)
    return slide
```

---

## 文件引用索引

本文件被核心 `SKILL.md` 在工作流程 Phase 3.13-3.14 中引用。
关联文件：`references/ppt-design-guide.md`（设计规范）、`scripts/ppt_generator.py`（已有脚本）
