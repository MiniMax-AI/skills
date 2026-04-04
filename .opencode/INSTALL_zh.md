# 安装 MiniMax Skills for OpenCode

## 前置要求

- 已安装 [OpenCode.ai](https://opencode.ai)

## 安装

### macOS / Linux

```bash
git clone https://github.com/MiniMax-AI/skills.git ~/.minimax-skills

mkdir -p ~/.config/opencode/skills
for skill in ~/.minimax-skills/skills/*/; do
    skill_name=$(basename "$skill")
    ln -s "$skill" ~/.config/opencode/skills/minimax-"$skill_name"
done
```

### Windows (PowerShell)

```powershell
git clone https://github.com/MiniMax-AI/skills.git "$env:USERPROFILE\.minimax-skills"

New-Item -ItemType Directory -Force -Path "$env:USERPROFILE\.config\opencode\skills"
Get-ChildItem "$env:USERPROFILE\.minimax-skills\skills" -Directory | ForEach-Object {
    New-Item -ItemType SymbolicLink -Path "$env:USERPROFILE\.config\opencode\skills\minimax-$($_.Name)" -Target $_.FullName
}
```

> **注意：** 在 Windows 上创建符号链接可能需要管理员权限或启用开发者模式。

重启 OpenCode 以发现技能。

验证方法：询问"列出可用技能"

## 可用技能

- **frontend-dev** — 前端开发，包含 UI 设计、动画、AI 生成媒体资源
- **fullstack-dev** — 全栈后端架构和前后端集成
- **android-native-dev** — Android 原生应用开发，采用 Material Design 3
- **ios-application-dev** — iOS 应用开发，包含 UIKit、SnapKit 和 SwiftUI
- **shader-dev** — GLSL 着色器技术，用于创建惊艳的视觉效果（兼容 ShaderToy）
- **gif-sticker-maker** — 将照片转换为动画 GIF 贴纸（Funko Pop / Pop Mart 风格）
- **minimax-pdf** — 使用基于令牌的设计系统生成、填写和重新格式化 PDF 文档
- **pptx-generator** — 生成、编辑和读取 PowerPoint 演示文稿
- **minimax-xlsx** — 打开、创建、读取、分析、编辑或验证 Excel/电子表格文件
- **minimax-docx** — 使用 OpenXML SDK 专业创建、编辑和格式化 Word 文档

## 更新

```bash
cd ~/.minimax-skills && git pull
```

符号链接将自动指向更新后的内容，无需重新链接。

## 卸载

### macOS / Linux

```bash
rm -f ~/.config/opencode/skills/minimax-*
rm -rf ~/.minimax-skills
```

### Windows (PowerShell)

```powershell
Get-ChildItem "$env:USERPROFILE\.config\opencode\skills\minimax-*" | Remove-Item -Force
Remove-Item -Recurse -Force "$env:USERPROFILE\.minimax-skills"
```

## 故障排除

### 找不到技能

1. 验证符号链接是否存在：`ls -la ~/.config/opencode/skills/`
2. 每个技能文件夹应包含 `SKILL.md` 文件
3. 安装后重启 OpenCode

## 获取帮助

- 问题反馈：https://github.com/MiniMax-AI/skills/issues
