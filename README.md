# MiniMax Skills

[中文版](./README_zh.md)

> **Beta** — This project is under active development. Skills, APIs, and configuration formats may change without notice. We welcome feedback and contributions.

Development skills for AI coding agents. Plug into your favorite AI coding tool and get structured, production-quality guidance for frontend, fullstack, and Android development.

## Skills

| Skill&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Description |
|---------------------------------------|-------------|
| `frontend-dev` | Full-stack frontend development combining premium UI design, cinematic animations (Framer Motion, GSAP), AI-generated media assets via MiniMax API (image, video, audio, music, TTS), persuasive copywriting (AIDA framework), and generative art (p5.js, Three.js, Canvas). Tech stack: React / Next.js, Tailwind CSS. |
| `fullstack-dev` | Full-stack backend architecture and frontend-backend integration. REST API design, auth flows (JWT, session, OAuth), real-time features (SSE, WebSocket), database integration (SQL / NoSQL), production hardening, and release checklist. Guided workflow: requirements → architecture → implementation. |
| `android-native-dev` | Android native application development with Material Design 3. Kotlin / Jetpack Compose, adaptive layouts, Gradle configuration, accessibility (WCAG), build troubleshooting, performance optimization, and motion system. |

## Installation

### Claude Code

```bash
claude plugin install --from "https://github.com/MiniMax-AI/skills"
```

### Cursor

```bash
git clone https://github.com/MiniMax-AI/skills.git ~/.cursor/minimax-skills
```

Add to your Cursor settings — point the skills path to `~/.cursor/minimax-skills/skills/`.

### Codex

```bash
git clone https://github.com/MiniMax-AI/skills.git ~/.codex/minimax-skills

mkdir -p ~/.agents/skills
ln -s ~/.codex/minimax-skills/skills ~/.agents/skills/minimax-skills
```

Restart Codex to discover the skills. See [`.codex/INSTALL.md`](.codex/INSTALL.md) for Windows instructions and details.

### OpenCode

Add to your `opencode.json`:

```json
{
  "plugin": ["minimax-skills@git+https://github.com/MiniMax-AI/skills.git"]
}
```

Restart OpenCode. See [`.opencode/INSTALL.md`](.opencode/INSTALL.md) for details.

## License

[MIT](./LICENSE)
