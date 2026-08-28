# Credits & Acknowledgments

MiniMax Skills builds upon ideas and work from the open-source community. We are grateful to the following projects and authors whose contributions helped shape skills in this repository.

## frontend-dev

The design engineering framework — including the design-variance system, motion recipes, card archetypes, color rules, and forbidden-pattern checklist — is derived from and inspired by:

- **[taste-skill](https://github.com/Leonxlnx/taste-skill)** by [Leonxlnx (Leon Lin)](https://github.com/Leonxlnx) — Anti-Slop Frontend design engineering skill framework.

The visual art section — including the philosophy-first workflow, static/interactive art modes, viewer template, and generator template — is derived from:

- **[canvas-design](https://github.com/anthropics/skills/tree/main/skills/canvas-design)** by Anthropic (Andi Brae) — Philosophy-first static visual art workflow. [Apache 2.0 License](./LICENSES/Apache-2.0.txt).
- **[algorithmic-art](https://github.com/anthropics/skills/tree/main/skills/algorithmic-art)** by Anthropic (Andi Brae) — Philosophy-first generative art workflow with p5.js. [Apache 2.0 License](./LICENSES/Apache-2.0.txt).

MiniMax extended the original frameworks with MiniMax API asset generation, copywriting modules (AIDA/PAS/FAB), multi-framework support, accessibility guidelines, and additional motion presets.

## react-native-dev

The core UI patterns, navigation, animations, and styling guidance is derived from:

- **[expo/skills](https://github.com/expo/skills/tree/main/plugins/expo/skills)** by [Expo](https://github.com/expo) (Kudo Chien / 650 Industries) — Expo development skills including building-native-ui. MIT License.

MiniMax extended the original with state management (Zustand/Jotai), forms, networking, testing, performance profiling, native capabilities, and engineering/CI/CD guidance.

## flutter-dev

The widget patterns, state management (Riverpod/Bloc), GoRouter navigation, performance optimization, and testing strategies are derived from:

- **[flutter-expert](https://github.com/Jeffallan/claude-skills/blob/main/skills/flutter-expert/SKILL.md)** by [Jeff Smolinski (@Jeffallan)](https://github.com/Jeffallan) — Flutter expert skill for Claude. MIT License.

MiniMax restructured the workflow-based guide into a reference-based format and expanded the reference system with additional topics.

## ponytail

The lazy-senior-dev coding mode (YAGNI / minimal-solution ladder, intensity levels, output rules) is derived from:

- **[ponytail](https://github.com/DietrichGebert/ponytail)** by [Dietrich Gebert](https://github.com/DietrichGebert) - "Lazy senior dev mode" skill for AI agents, with published benchmark gains (~54% less code, ~20% cheaper, ~27% faster, 100% safe against the same-agent baseline). MIT License.

This entry reformats the original Claude-Code plugin `SKILL.md` for the MiniMax Skills repo conventions: the Claude-Code-specific `argument-hint` field is dropped, the description is left unchanged (it already includes both trigger phrases and "do not use for" exclusions), and a `metadata` block (`version` / `category: methodology` / `sources`) is added. The body is unchanged - the seven-rung ladder, the bug-fix-root-cause rule, the intensity table, the output contract, and the "when NOT to be lazy" carve-outs are kept verbatim, so the upstream benchmark numbers apply directly.

---

If you believe your work has been included in this repository without proper attribution, please [open an issue](https://github.com/MiniMax-AI/skills/issues) and we will address it promptly.
