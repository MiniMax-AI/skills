---
name: minimax-docx-latex
license: MIT
metadata:
  version: "1.0.0"
  category: document-processing
  author: MiniMaxAI
description: >
  在 DOCX 中插入 LaTeX 格式数学公式。核心发现：LibreOffice 打开 DOCX 时不锁定文件，
  minimax-docx 可以同时修改，实现实时预览编辑。
  默认规则：所有公式变量必须用 $ 包裹，如 $\alpha$、$\beta$、$\sqrt{x+y}$。
triggers:
  - 添加公式
  - 插入 latex
  - latex 公式
  - docx 公式
  - 修改 docx
  - 转换 markdown 到 docx
---

# minimax-docx-latex

在 DOCX 中插入 LaTeX 格式的数学公式。

## 默认规则

**重要：所有公式变量必须用 $ 包裹**

| 类型 | 正确 | 错误 |
|------|------|------|
| 单变量 | $\alpha$ | \alpha |
| 分数 | $\frac{x}{y}$ | \frac{x}{y} |
| 开方 | $\sqrt{x+y}$ | \sqrt{x+y} |
| 积分 | $\int_{a}^{b} f(x) dx$ | \int_{a}^{b} f(x) dx |
| 求和 | $\sum_{i=1}^{n} i^2$ | \sum_{i=1}^{n} i^2 |
| 矩阵 | $\begin{pmatrix} a & b \end{pmatrix}$ | \begin{pmatrix} a & b \end{pmatrix} |
| 独立公式 | $$\int_{0}^{\infty} e^{-x^2} dx$$ | $$\int_{0}^{\infty} e^{-x^2} dx$$ |

**示例：**
- ✅ $\alpha + \beta = \gamma$
- ❌ \alpha + \beta = \gamma

## 核心发现

| 软件 | 打开 DOCX 时 | 外部程序能同时修改？ |
|------|-------------|---------------------|
| Word | 锁定文件 | ❌ 否 |
| LibreOffice | **不锁定** | ✅ **可以** |

**原理：**
- DOCX 本质是 ZIP 包（包含 word/document.xml）
- LibreOffice 打开时显示内存缓存，不影响磁盘文件
- minimax-docx 直接操作磁盘上的 ZIP 包
- 外部修改后，LibreOffice 按 Ctrl+Shift+R 刷新即可看到变化

## 使用流程

### 1. 启动 LibreOffice（保持连接）

```bash
# 方式 A：图形界面打开（推荐）
libreoffice /path/to/document.docx

# 方式 B：命令行 headless 模式
libreoffice --headless --norestore \
  --accept="socket,host=localhost,port=2003;urp;" \
  --nofirststartwizard &
```

### 2. 用 minimax-docx 修改 DOCX

```bash
# 在 LibreOffice 打开文件的同时，直接修改
dotnet run --project MiniMaxAIDocx.Cli -- edit replace-text \
  --input document.docx \
  --output document.docx \
  --search "OLD_TEXT" \
  --replace "$\alpha + \beta$"
```

### 3. 刷新预览

在 LibreOffice 中按 **Ctrl+Shift+R**（或 文件 → 重新装入）

## LaTeX 公式格式

Word/LibreOffice 支持的 LaTeX 公式语法：

| 类型 | 语法 | 示例 |
|------|------|------|
| 行内公式 | `$...$` | `$x^2 + y^2$` |
| 独立公式 | `$$...$$` | `$$\int_0^\infty e^{-x} dx$$` |
| 分数 | `\frac{分子}{分母}` | `$\frac{a}{b}$` |
| 上标 | `^{指数}` | `$x^{2}$` |
| 下标 | `_{下标}` | `$x_{i}$` |
| 平方根 | `\sqrt{内容}` | `$\sqrt{x+y}$` |
| 求和 | `\sum_{下标}^{上标}` | `$\sum_{i=1}^{n}$` |
| 积分 | `\int_{下标}^{上标}` | `$\int_{a}^{b}$` |
| 无穷 | `\infty` | `$\infty$` |
| 希腊字母 | `\alpha \beta \gamma` | `$\alpha + \beta$` |

## 完整公式库

见 `references/formula_library.md`

## 限制

- 仅 LibreOffice 支持实时预览（Word 会锁定）
- LaTeX 文本格式，非渲染图片
- 如需渲染，需在 Office 软件中手动转换格式
