# MiniMax Skills

[中文版](./README_zh.md)

> **Beta** — This project is under active development. Skills, APIs, and configuration formats may change without notice. We welcome feedback and contributions.

Development skills for AI coding agents. Plug into your favorite AI coding tool and get structured, production-quality guidance for frontend, fullstack, Android, iOS, and shader development.

## Skills

| Skill&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Description |
|---------------------------------------|-------------|
| `frontend-dev` | Full-stack frontend development combining premium UI design, cinematic animations (Framer Motion, GSAP), AI-generated media assets via MiniMax API (image, video, audio, music, TTS), persuasive copywriting (AIDA framework), and generative art (p5.js, Three.js, Canvas). Tech stack: React / Next.js, Tailwind CSS. |
| `fullstack-dev` | Full-stack backend architecture and frontend-backend integration. REST API design, auth flows (JWT, session, OAuth), real-time features (SSE, WebSocket), database integration (SQL / NoSQL), production hardening, and release checklist. Guided workflow: requirements → architecture → implementation. |
| `android-native-dev` | Android native application development with Material Design 3. Kotlin / Jetpack Compose, adaptive layouts, Gradle configuration, accessibility (WCAG), build troubleshooting, performance optimization, and motion system. |
| `ios-application-dev` | iOS application development guide covering UIKit, SnapKit, and SwiftUI. Touch targets, safe areas, navigation patterns, Dynamic Type, Dark Mode, accessibility, collection views, and Apple HIG compliance. |
| `shader-dev` | Comprehensive GLSL shader techniques for creating stunning visual effects — ray marching, SDF modeling, fluid simulation, particle systems, procedural generation, lighting, post-processing, and more. ShaderToy-compatible. |
| `gif-sticker-maker` | Convert photos (people, pets, objects, logos) into 4 animated GIF stickers with captions. Funko Pop / Pop Mart style, powered by MiniMax Image & Video Generation API. |
| `podcast-creator` | Convert text scripts into podcast episodes with narration and music. Supports plain text, Markdown, or structured JSON input. Generates narration via MiniMax TTS API and intro/outro music via MiniMax Music API, then assembles with ffmpeg. |
| `minimax-pdf` | Generate, fill, and reformat PDF documents with a token-based design system. CREATE polished PDFs from scratch (15 cover styles), FILL existing form fields, or REFORMAT documents into a new design. Print-ready output with typography and color derived from document type. |
| `pptx-generator` | Generate, edit, and read PowerPoint presentations. Create from scratch with PptxGenJS (cover, TOC, content, section divider, summary slides), edit existing PPTX via XML workflows, or extract text with markitdown. |
| `minimax-xlsx` | Open, create, read, analyze, edit, or validate Excel/spreadsheet files (.xlsx, .xlsm, .csv, .tsv). Covers creating new xlsx from scratch via XML templates, reading and analyzing with pandas, editing existing files with zero format loss, formula recalculation, validation, and professional financial formatting. |
| `minimax-docx` | Professional DOCX document creation, editing, and formatting using OpenXML SDK (.NET). Three pipelines: create new documents from scratch, fill/edit content in existing documents, or apply template formatting with XSD validation gate-check. |

## Installation

### Claude Code

```bash
claude plugin marketplace add https://github.com/MiniMax-AI/skills
claude plugin install minimax-skills
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

```bash
git clone https://github.com/MiniMax-AI/skills.git ~/.minimax-skills

mkdir -p ~/.config/opencode/skills
ln -s ~/.minimax-skills/skills/* ~/.config/opencode/skills/
```

Restart OpenCode to discover the skills. See [`.opencode/INSTALL.md`](.opencode/INSTALL.md) for details.

## License

[MIT](./LICENSE)
