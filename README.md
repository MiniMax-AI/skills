# MiniMax Skills

[中文版](./README_zh.md)

> **Beta** — This project is under active development. Skills, APIs, and configuration formats may change without notice. We welcome feedback and contributions.

Development skills for AI coding agents. Plug into your favorite AI coding tool and get structured, production-quality guidance for frontend, fullstack, Android, iOS, and shader development.

## Skills

| Skill&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Description | Source |
|---------------------------------------|-------------|--------|
| `frontend-dev` | Full-stack frontend development combining premium UI design, cinematic animations (Framer Motion, GSAP), AI-generated media assets via MiniMax API (image, video, audio, music, TTS), persuasive copywriting (AIDA framework), and generative art (p5.js, Three.js, Canvas). Tech stack: React / Next.js, Tailwind CSS. | Official |
| `fullstack-dev` | Full-stack backend architecture and frontend-backend integration. REST API design, auth flows (JWT, session, OAuth), real-time features (SSE, WebSocket), database integration (SQL / NoSQL), production hardening, and release checklist. Guided workflow: requirements → architecture → implementation. | Official |
| `android-native-dev` | Android native application development with Material Design 3. Kotlin / Jetpack Compose, adaptive layouts, Gradle configuration, accessibility (WCAG), build troubleshooting, performance optimization, and motion system. | Official |
| `ios-application-dev` | iOS application development guide covering UIKit, SnapKit, and SwiftUI. Touch targets, safe areas, navigation patterns, Dynamic Type, Dark Mode, accessibility, collection views, and Apple HIG compliance. | Official |
| `flutter-dev` | Flutter cross-platform development covering widget patterns, Riverpod/Bloc state management, GoRouter navigation, performance optimization, and testing strategies. | Official |
| `react-native-dev` | React Native and Expo development guide covering components, styling, animations, navigation, state management, forms, networking, performance optimization, testing, native capabilities, and engineering (project structure, deployment, SDK upgrades, CI/CD). | Official |
| `shader-dev` | Comprehensive GLSL shader techniques for creating stunning visual effects — ray marching, SDF modeling, fluid simulation, particle systems, procedural generation, lighting, post-processing, and more. ShaderToy-compatible. | Official |
| `gif-sticker-maker` | Convert photos (people, pets, objects, logos) into 4 animated GIF stickers with captions. Funko Pop / Pop Mart style, powered by MiniMax Image & Video Generation API. | Official |
| `minimax-pdf` | Generate, fill, and reformat PDF documents with a token-based design system. CREATE polished PDFs from scratch (15 cover styles), FILL existing form fields, or REFORMAT documents into a new design. Print-ready output with typography and color derived from document type. | Official |
| `pptx-generator` | Generate, edit, and read PowerPoint presentations. Create from scratch with PptxGenJS (cover, TOC, content, section divider, summary slides), edit existing PPTX via XML workflows, or extract text with markitdown. | Official |
| `minimax-xlsx` | Open, create, read, analyze, edit, or validate Excel/spreadsheet files (.xlsx, .xlsm, .csv, .tsv). Covers creating new xlsx from scratch via XML templates, reading and analyzing with pandas, editing existing files with zero format loss, formula recalculation, validation, and professional financial formatting. | Official |
| `minimax-docx` | Professional DOCX document creation, editing, and formatting using OpenXML SDK (.NET). Three pipelines: create new documents from scratch, fill/edit content in existing documents, or apply template formatting with XSD validation gate-check. | Official |
| `vision-analysis` | Analyze, describe, and extract information from images using vision AI models. Supports describe, OCR, UI mockup review, chart data extraction, and object detection. Powered by MiniMax VL API with OpenAI GPT-4V fallback. | Community |
| `markdown-mcp` | MCP tool for efficient markdown file reading and editing. Replace Python scripts with direct file operations — get file info, grep, read sections, replace text, insert lines via MCP tools. Python stdlib only, no dependencies. | Community |
| `context-maintainer` | Maintain persistent project context across AI agent sessions. Creates and updates `.context/` files (goals, architecture, decisions, active files, stale files). Triggers on git commit, context threshold, or session end. Gitignored by default. | Community |
| `context-search` | Search and retrieve persistent context across sessions. Works with `.context/` files — get active context, search decisions, find file history. Optional QMD integration for semantic search. Export to Obsidian vault supported. | Community |
| `minimax-multimodal-toolkit` | Generate voice, music, video, and image content via MiniMax APIs — the unified entry for MiniMax multimodal use cases. Covers TTS (text-to-speech, voice cloning, voice design, multi-segment), music (songs, instrumentals), video (text-to-video, image-to-video, start-end frame, subject reference, templates, long-form multi-scene), image (text-to-image, image-to-image with character reference), and media processing (convert, concat, trim, extract) via FFmpeg. | Official |
| `minimax-music-gen` | Generate vocal songs, instrumentals, and covers using MiniMax Music API. Two modes: Basic (one-liner in, song out) and Advanced Control (edit lyrics, refine prompt, plan structure). Supports lyrics generation, style vocabulary, streaming playback, and iterative feedback. | Official |
| `buddy-sings` | Let your Claude Code pet (/buddy) sing a personalized song. Interprets the pet's name and personality into a unique cached vocal identity, auto-gathers context (conversation, memory, git history) for themed lyrics, and generates music via minimax-music-gen. | Official |
| `minimax-music-playlist` | Generate personalized playlists by analyzing your music taste. Builds a taste profile (genre, mood, language, vocal preferences), plans a themed tracklist, generates songs with album cover art, and refines the profile from feedback. | Official |

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
For Windows setup and verification, see [`.cursor-plugin/INSTALL.md`](.cursor-plugin/INSTALL.md).

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

### VS Code

This repository does not currently ship a standalone VS Code extension.

If you use VS Code, the supported approach is to run one of the supported CLI tools inside the integrated terminal:
- Codex
- Claude Code
- OpenCode

If you want native local-skills configuration from this repo, use Cursor and follow [`.cursor-plugin/INSTALL.md`](.cursor-plugin/INSTALL.md).

## Contributing

We welcome contributions! Before submitting a PR, please read:

- [CONTRIBUTING.md](./CONTRIBUTING.md) — PR format, skill structure requirements, and development guidelines
- [PR Review Rules](./.claude/skills/pr-review/SKILL.md) — automated validation checks and quality review criteria

You can run the validation script locally before submitting:

```bash
python .claude/skills/pr-review/scripts/validate_skills.py
```

## ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=MiniMax-AI/skills&type=Date)](https://star-history.com/#MiniMax-AI/skills&Date)

## Credits

Some skills in this repository are inspired by or derived from work by the open-source community. See [CREDITS.md](./CREDITS.md) for full acknowledgments.

## License

[MIT](./LICENSE)
