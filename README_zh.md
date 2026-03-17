# MiniMax Skills

[English](./README.md)

> **Beta** — 本项目正在积极开发中。技能内容、API 和配置格式可能会在不另行通知的情况下变更。欢迎反馈和贡献。

面向 AI 编程工具的开发技能库。接入你常用的 AI 编程工具，获得结构化的、生产级质量的前端、全栈、Android、iOS 和着色器开发指导。

## 技能列表

| 技能&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | 简介 |
|---------------------------------------|------|
| `frontend-dev` | 全栈前端开发，融合高级 UI 设计、电影级动画（Framer Motion、GSAP）、通过 MiniMax API 生成媒体资源（图片、视频、音频、音乐、TTS）、基于 AIDA 框架的说服力文案、生成艺术（p5.js、Three.js、Canvas）。技术栈：React / Next.js、Tailwind CSS。 |
| `fullstack-dev` | 全栈后端架构与前后端集成。REST API 设计、认证流程（JWT、Session、OAuth）、实时功能（SSE、WebSocket）、数据库集成（SQL / NoSQL）、生产环境加固与发布清单。引导式工作流：需求收集 → 架构决策 → 实现。 |
| `android-native-dev` | 基于 Material Design 3 的 Android 原生应用开发。Kotlin / Jetpack Compose、自适应布局、Gradle 配置、无障碍（WCAG）、构建问题排查、性能优化与动效系统。 |
| `ios-application-dev` | iOS 应用开发指南，涵盖 UIKit、SnapKit 和 SwiftUI。触控目标、安全区域、导航模式、Dynamic Type、深色模式、无障碍、集合视图，符合 Apple HIG 规范。 |
| `shader-dev` | 全面的 GLSL 着色器技术，用于创建惊艳的视觉效果 — 光线行进、SDF 建模、流体模拟、粒子系统、程序化生成、光照、后处理等。兼容 ShaderToy。 |

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

在 `opencode.json` 中添加：

```json
{
  "plugin": ["minimax-skills@git+https://github.com/MiniMax-AI/skills.git"]
}
```

重启 OpenCode。详见 [`.opencode/INSTALL.md`](.opencode/INSTALL.md)。

## 许可证

[MIT](./LICENSE)
