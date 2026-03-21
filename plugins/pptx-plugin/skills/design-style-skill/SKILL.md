---
name: design-style-skill
description: >
  Select a consistent visual design system for PPT slides using radius/spacing style recipes.
  Use when users ask for overall style direction or component styling consistency.
  Includes Sharp/Soft/Rounded/Pill recipes, component mappings, typography/spacing rules, and mixing guidance.
  Triggers: 风格, style, radius, spacing, 圆角, 间距, PPT风格, 视觉风格, design style, component style.
---

# Style Recipes - PPT视觉风格系统

同一套设计可通过调整圆角（rectRadius）和间距呈现4种不同风格。根据场景选择合适的风格配方。

> **单位说明**: PptxGenJS 使用英寸(inch)作为单位。幻灯片尺寸为 10" × 5.625" (LAYOUT_16x9)

## 风格概览

| 风格 | 圆角范围 | 间距范围 | 适合场景 |
|---|---|---|---|
| **Sharp & Compact** | 0 ~ 0.05" | 紧凑 | 数据密集型、表格、专业报告 |
| **Soft & Balanced** | 0.08" ~ 0.12" | 适中 | 企业汇报、商务演示、通用PPT |
| **Rounded & Spacious** | 0.15" ~ 0.25" | 宽松 | 产品介绍、营销演示、创意展示 |
| **Pill & Airy** | 0.3" ~ 0.5" | 通透 | 品牌展示、发布会、高端演示 |

---

## Sharp & Compact（锐利紧凑）

**视觉特征**: 方正、信息密度高、专业严肃感。

### Token 配方

| 类别 | 值 (英寸) | 说明 |
|---|---|---|
| 圆角-小 | 0" | 完全直角 |
| 圆角-中 | 0.03" | 微圆角 |
| 圆角-大 | 0.05" | 小圆角 |
| 元素内边距 | 0.1" ~ 0.15" | 紧凑 |
| 元素间距 | 0.1" ~ 0.2" | 紧凑 |
| 页面边距 | 0.3" | 较窄 |
| 区块间距 | 0.25" ~ 0.35" | 紧凑 |

---

## Soft & Balanced（柔和均衡）

**视觉特征**: 适中的圆角、舒适的留白、专业又不失亲和。

### Token 配方

| 类别 | 值 (英寸) | 说明 |
|---|---|---|
| 圆角-小 | 0.05" | 小圆角 |
| 圆角-中 | 0.08" | 中等圆角 |
| 圆角-大 | 0.12" | 较大圆角 |
| 元素内边距 | 0.15" ~ 0.2" | 适中 |
| 元素间距 | 0.15" ~ 0.25" | 适中 |
| 页面边距 | 0.4" | 标准 |
| 区块间距 | 0.35" ~ 0.5" | 适中 |

---

## Rounded & Spacious（圆润宽松）

**视觉特征**: 大圆角、充裕留白、友好亲切、现代感。

### Token 配方

| 类别 | 值 (英寸) | 说明 |
|---|---|---|
| 圆角-小 | 0.1" | 中等圆角 |
| 圆角-中 | 0.15" | 大圆角 |
| 圆角-大 | 0.25" | 很大圆角 |
| 元素内边距 | 0.2" ~ 0.3" | 宽松 |
| 元素间距 | 0.25" ~ 0.4" | 宽松 |
| 页面边距 | 0.5" | 较宽 |
| 区块间距 | 0.5" ~ 0.7" | 宽松 |

---

## Pill & Airy（胶囊通透）

**视觉特征**: 全圆角胶囊形、大量留白、轻盈通透、品牌展示感强。

### Token 配方

| 类别 | 值 (英寸) | 说明 |
|---|---|---|
| 圆角-小 | 0.2" | 大圆角 |
| 圆角-中 | 0.3" | 胶囊形 |
| 圆角-大 | 0.5" | 完全胶囊 |
| 元素内边距 | 0.25" ~ 0.4" | 通透 |
| 元素间距 | 0.3" ~ 0.5" | 通透 |
| 页面边距 | 0.6" | 宽 |
| 区块间距 | 0.6" ~ 0.9" | 通透 |

---

# 组件级风格映射表

| 组件 | Sharp | Soft | Rounded | Pill |
|---|---|---|---|---|
| **按钮/标签** | rectRadius: 0 | rectRadius: 0.05 | rectRadius: 0.1 | rectRadius: 0.2 |
| **卡片/容器** | rectRadius: 0.03 | rectRadius: 0.1 | rectRadius: 0.2 | rectRadius: 0.3 |
| **图片容器** | rectRadius: 0 | rectRadius: 0.08 | rectRadius: 0.15 | rectRadius: 0.25 |
| **输入框形状** | rectRadius: 0 | rectRadius: 0.05 | rectRadius: 0.1 | rectRadius: 0.2 |
| **徽章/Badge** | rectRadius: 0.02 | rectRadius: 0.05 | rectRadius: 0.08 | rectRadius: 0.15 |
| **头像框** | rectRadius: 0 | rectRadius: 0.1 | rectRadius: 0.2 | rectRadius: 0.5 (圆形) |

### PptxGenJS 圆角示例

```javascript
// Sharp 风格卡片
slide.addShape("rect", {
  x: 0.5, y: 1, w: 4, h: 2.5,
  fill: { color: "F5F5F5" },
  rectRadius: 0.03
});

// Rounded 风格卡片
slide.addShape("rect", {
  x: 0.5, y: 1, w: 4, h: 2.5,
  fill: { color: "F5F5F5" },
  rectRadius: 0.2
});

// Pill 风格按钮 (高度0.4"时，rectRadius设为0.2"即为胶囊形)
slide.addShape("rect", {
  x: 3, y: 4, w: 2, h: 0.4,
  fill: { color: "4A90D9" },
  rectRadius: 0.2
});
```

---

# 混搭原则

## 1. 外层容器 ≥ 内层圆角

```javascript
// 正确：外 > 内
card:   rectRadius: 0.2
button: rectRadius: 0.1

// 错误：内 > 外 → 视觉溢出感
card:   rectRadius: 0.1
button: rectRadius: 0.2
```

## 2. 信息密度决定间距

| 区域类型 | 推荐风格 |
|---|---|
| 数据展示区 | Sharp / Soft（紧凑间距） |
| 内容浏览区 | Rounded / Pill（宽松间距） |
| 标题区域 | Soft / Rounded（适中间距） |

## 3. 圆角与元素高度的关系

| 元素高度 | Sharp | Soft | Rounded | Pill |
|---|---|---|---|---|
| 小 (< 0.3") | 0" | 0.03" | 0.08" | 高度/2 |
| 中 (0.3" ~ 0.6") | 0.02" | 0.05" | 0.12" | 高度/2 |
| 大 (0.6" ~ 1.2") | 0.03" | 0.08" | 0.2" | 0.3" |
| 超大 (> 1.2") | 0.05" | 0.12" | 0.25" | 0.4" |

> **Pill风格提示**: 要实现完美胶囊形，设置 `rectRadius = 元素高度 / 2`

---

# Typography 排版规范 (PPT)

| 用途 | 字号 (pt) | 说明 |
|---|---|---|
| 注释/来源 | 10 ~ 12 | 最小可读字号 |
| 正文/描述 | 14 ~ 16 | 标准正文 |
| 副标题 | 18 ~ 22 | 次要标题 |
| 标题 | 28 ~ 36 | 页面标题 |
| 大标题 | 44 ~ 60 | 封面/章节标题 |
| 数据高亮 | 60 ~ 96 | 关键数字展示 |

---

# Spacing 间距规范 (PPT)

基于10" × 5.625"幻灯片尺寸：

| 用途 | 推荐值 (英寸) |
|---|---|
| 图标与文字间距 | 0.08" ~ 0.15" |
| 列表项间距 | 0.15" ~ 0.25" |
| 卡片内边距 | 0.2" ~ 0.4" |
| 元素组间距 | 0.3" ~ 0.5" |
| 页面安全边距 | 0.4" ~ 0.6" |
| 主要区块间距 | 0.5" ~ 0.8" |

---

# 快速选择指南

| 演示类型 | 推荐风格 | 原因 |
|---|---|---|
| 财务/数据报告 | Sharp & Compact | 信息密度高，专业严谨 |
| 企业汇报/商务 | Soft & Balanced | 平衡专业与友好 |
| 产品介绍/营销 | Rounded & Spacious | 现代感，亲切感 |
| 发布会/品牌展示 | Pill & Airy | 高端感，视觉冲击 |
| 培训/教育 | Soft / Rounded | 清晰易读，友好 |
| 技术分享 | Sharp / Soft | 专业，信息清晰 |
