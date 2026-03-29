# MiniMax Skills

[English](./README.md)

> **Beta** — 本项目正在积极开发中。技能内容、API 和配置格式可能会在不另行通知的情况下变更。欢迎反馈和贡献。

面向 AI 编程工具的开发技能库。接入你常用的 AI 编程工具，获得结构化的、生产级质量的前端、全栈、Android、iOS 和着色器开发指导。

## 技能列表

| 技能&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | 简介 | 来源 |
|---------------------------------------|------|------|
| `frontend-dev` | 全栈前端开发，融合高级 UI 设计、电影级动画（Framer Motion、GSAP）、通过 MiniMax API 生成媒体资源（图片、视频、音频、音乐、TTS）、基于 AIDA 框架的说服力文案、生成艺术（p5.js、Three.js、Canvas）。技术栈：React / Next.js、Tailwind CSS。 | Official |
| `fullstack-dev` | 全栈后端架构与前后端集成。REST API 设计、认证流程（JWT、Session、OAuth）、实时功能（SSE、WebSocket）、数据库集成（SQL / NoSQL）、生产环境加固与发布清单。引导式工作流：需求收集 → 架构决策 → 实现。 | Official |
| `android-native-dev` | 基于 Material Design 3 的 Android 原生应用开发。Kotlin / Jetpack Compose、自适应布局、Gradle 配置、无障碍（WCAG）、构建问题排查、性能优化与动效系统。 | Official |
| `ios-application-dev` | iOS 应用开发指南，涵盖 UIKit、SnapKit 和 SwiftUI。触控目标、安全区域、导航模式、Dynamic Type、深色模式、无障碍、集合视图，符合 Apple HIG 规范。 | Official |
| `shader-dev` | 全面的 GLSL 着色器技术，用于创建惊艳的视觉效果 — 光线行进、SDF 建模、流体模拟、粒子系统、程序化生成、光照、后处理等。兼容 ShaderToy。 | Official |
| `gif-sticker-maker` | 将照片（人物、宠物、物品、Logo）转换为 4 张带字幕的动画 GIF 贴纸。Funko Pop / Pop Mart 盲盒风格，基于 MiniMax 图片与视频生成 API。 | Official |
| `minimax-pdf` | 基于 token 化设计系统生成、填写和重排 PDF 文档。支持三种模式：CREATE（从零生成，15 种封面风格）、FILL（填写现有表单字段）、REFORMAT（将已有文档重排为新设计）。排版与配色由文档类型自动推导，输出即可打印。 | Official |
| `pptx-generator` | 生成、编辑和读取 PowerPoint 演示文稿。支持用 PptxGenJS 从零创建（封面、目录、内容、分节页、总结页），通过 XML 工作流编辑现有 PPTX，或用 markitdown 提取文本。 | Official |
| `minimax-xlsx` | 打开、创建、读取、分析、编辑或验证 Excel/电子表格文件（.xlsx、.xlsm、.csv、.tsv）。支持通过 XML 模板从零创建 xlsx、使用 pandas 读取分析、零格式损失编辑现有文件、公式重算与验证、专业财务格式化。 | Official |
| `minimax-docx` | 基于 OpenXML SDK（.NET）的专业 DOCX 文档创建、编辑与排版。三条流水线：从零创建新文档、填写/编辑现有文档内容、应用模板格式并通过 XSD 验证门控检查。 | Official |
| `vision-analysis` | 使用视觉 AI 模型分析、描述和提取图像信息。支持描述、OCR 文字识别、UI 界面审查、图表数据提取和物体检测。基于 MiniMax VL API，OpenAI GPT-4V 作为备选。 | Community |
| `markdown-mcp` | 高效读取和编辑 Markdown 文件的 MCP 工具。无需编写 Python 脚本——通过 MCP 工具直接获取文件信息、搜索、读取章节、替换文本、插入行。替代缓慢的 Python 脚本编辑模式。需安装 `minimax-markdown-mcp` 包。 | Community |
| `markdown-editing` | 高效编辑 Markdown 文件，使用精准、最小化的操作。指导 Agent 少量读取、精准编辑、稀疏验证——避免全文重写和重复读取。适用于大型文档项目。 | Community |

## 安装

### Claude Code

```bash
claude plugin marketplace add https://github.com/MiniMax-AI/skills
claude plugin install minimax-skills
```

### Cursor

```bash
git clone https://github.com/MiniMax-AI/skills.git ~/.cursor/minimax-skills
```

在 Cursor 设置中将 skills 路径指向 `~/.cursor/minimax-skills/skills/`。

### Codex

```bash
git clone https://github.com/MiniMax-AI/skills.git ~/.codex/minimax-skills

mkdir -p ~/.agents/skills
ln -s ~/.codex/minimax-skills/skills ~/.agents/skills/minimax-skills
```

重启 Codex 以发现技能。Windows 安装说明见 [`.codex/INSTALL.md`](.codex/INSTALL.md)。

### OpenCode

```bash
git clone https://github.com/MiniMax-AI/skills.git ~/.minimax-skills

mkdir -p ~/.config/opencode/skills
ln -s ~/.minimax-skills/skills/* ~/.config/opencode/skills/
```

重启 OpenCode 以发现技能。详见 [`.opencode/INSTALL.md`](.opencode/INSTALL.md)。

## 贡献

欢迎贡献！提交 PR 前请阅读：

- [CONTRIBUTING.md](./CONTRIBUTING.md) — PR 格式、Skill 结构要求与开发指南
- [PR Review 规则](./.claude/skills/pr-review/SKILL.md) — 自动化校验检查与质量审核标准

提交前可在本地运行校验脚本：

```bash
python .claude/skills/pr-review/scripts/validate_skills.py
```

## 许可证

[MIT](./LICENSE)
