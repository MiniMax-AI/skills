---
name: minimax-music-playlist-cn
description: >
  基于用户音乐品味生成个性化播放列表的中文优化版 Skill。
  支持 QQ音乐、网易云音乐、汽水音乐在线分享链接解析，以及本地音乐库扫描。
  触发条件：用户分享音乐链接、请求生成播放列表、分析音乐品味、个性化音乐推荐。
  多语言支持——根据用户消息语言自动适配输出语言。
license: MIT
metadata:
  version: "1.0-cn"
  category: creative
  based_on: minimax-music-playlist v2.0
---

# MiniMax Music Playlist CN — 个性化播放列表生成器（中文优化版）

基于官方 minimax-music-playlist v2.0 优化的中文版本，优先支持在线音乐平台分享链接解析。

## 🎯 核心特性

- **在线优先**：支持 QQ音乐、网易云音乐、汽水音乐分享链接
- **跨平台**：Windows / Linux / macOS / Docker 均可使用
- **智能分析**：使用 artist_genre_map.json 流派推断
- **稳定生成**：串行生成，可靠不丢失
- **零依赖**：纯 Python 标准库，无需 pip install

---

## 👤 用户指引

当你想让我分析你的音乐品味并生成个性化音乐时，请按以下步骤分享你的歌单：

### QQ音乐（移动端）
```
我的 → 收藏 → 右上角分享图标 → 分享至微信好友 → 选择"文件传输助手" → 复制链接粘贴至当前聊天
```

### 网易云音乐
```
我的 → 我喜欢的音乐 → 页面中段的分享按钮 → 复制链接 → 粘贴至当前聊天
```

### 汽水音乐
```
我的 → 我喜欢的音乐 → 页面中段的分享按钮 → 复制链接 → 粘贴至当前聊天
```

分享链接示例：
- QQ音乐：`https://y.qq.com/n3/other/pages/details/playlist.html?id=xxxxx`
- 网易云：`https://music.163.com/playlist?id=xxxxx`
- 汽水音乐：`https://qishui.douyin.com/s/xxxxx/`

### 或者直接告诉我你的品味
```
我喜欢周杰伦、林俊杰、薛之谦的歌，风格偏中国风和抒情
```

---

## 📋 支持的链接格式

| 平台 | 链接示例 | API 支持 |
|------|---------|---------|
| **QQ音乐** | `https://y.qq.com/n3/...?id=6390157139` | ✅ 公开 API |
| **网易云音乐** | `https://music.163.com/playlist?id=5771759` | ✅ v3 API |
| **汽水音乐** | `https://qishui.douyin.com/s/ix5EGhHT/` | ⚠️ 需浏览器 |

---

## 🤖 Agent 技术文档

### 前置条件

- **mmx CLI** — 音乐与图像生成
  ```bash
  npm install -g mmx-cli
  mmx auth login --api-key <key>
  ```
- **Python 3** — 用于解析脚本（纯标准库，无需 pip install）
- **播放器** — `mpv`、`ffplay` 或 `afplay`（macOS）

### 触发条件

收到以下内容时，调用本 skill：
- 包含 `y.qq.com` 的链接 — QQ音乐
- 包含 `music.163.com` 的链接 — 网易云音乐
- 包含 `qishui.douyin.com` 或 `music.douyin.com` 的链接 — 汽水音乐
- 包含"歌单"、"播放列表"、"音乐品味"、"个性化音乐"等关键词
- 用户描述自己喜欢的歌手/音乐风格

### 工作流程

```
1. 收集数据 → 2. 构建品味画像 → 3. 规划播放列表
    → 4. 生成歌曲（串行）→ 5. 播放
```

---

## Step 1: 收集音乐数据

**数据源优先级：**

| 优先级 | 数据源 | 方法 | 适用场景 |
|--------|--------|------|---------|
| 1 | **在线分享链接** | API 解析 | 用户粘贴链接 |
| 2 | **本地音乐库** | 文件扫描 | macOS/有本地文件 |
| 3 | **手动输入** | 用户口述 | 无数据源时 |

### 1.1 在线分享链接解析（优先）

使用 `playlist_parser.py` 提供的 `PlaylistParser` 类：

```python
from playlist_parser import PlaylistParser

parser = PlaylistParser()
playlist = parser.parse(url)  # 自动识别平台
# 返回: Playlist(name, tracks, source, creator, play_count)
```

**支持的 API：**

| 平台 | API Endpoint | 必需 Header |
|------|-------------|-------------|
| QQ音乐 | `c.y.qq.com/qzone/fcg-bin/fcg_ucc_getcdinfo_byids_cp.fcg` | `Referer: https://y.qq.com/` |
| 网易云 | `music.163.com/api/v3/playlist/detail` | `Referer: https://music.163.com/` |
| 汽水音乐 | 浏览器渲染 + JS 提取 | 需 `browser_navigate` 工具 |

具体实现见 `playlist_parser.py`。

### 1.2 本地音乐库扫描（备选）

**仅当无在线链接时使用**

| 平台 | 方法 | 路径 |
|------|------|------|
| Apple Music | `osascript` 查询 | macOS 原生 |
| NetEase 本地 | 读取 JSON | `~/Library/Containers/com.netease.163music/...` |
| QQ音乐本地 | 读取数据库 | Windows: `%APPDATA%\Tencent\QQMusic\` |

### 1.3 手动输入（兜底）

如果无数据源，询问用户：
```
请告诉我你喜欢的歌手或音乐风格，例如：
"我喜欢周杰伦、林俊杰，风格偏中国风和抒情"
```

**隐私规则：** 不向用户展示原始歌曲列表，只展示聚合统计。

---

## Step 2: 构建品味画像

使用 `TasteAnalyzer` 类：

```python
from playlist_parser import TasteAnalyzer

analyzer = TasteAnalyzer()
profile = analyzer.analyze([playlist])
# 返回: TasteProfile(total_tracks, top_artists, genres, ...)
analyzer.print_report(profile)  # 打印报告
```

**品味画像包含：**
- **流派分布** — 用户听的音乐风格（如 mandopop 40%、pop 30%）
- **Top 艺术家** — 最常听的艺术家

### 流派推断方法

1. **查询本地映射表** — `<SKILL_DIR>/data/artist_genre_map.json`
   - 包含 23,000+ 艺术家的预映射流派、人声类型、语言
   - 包含 1,400+ 华语艺术家（mandopop/cantopop）

2. **最终回退** — 使用艺术家名作为风格参考

### 展示用户摘要

```
你的音乐画像：
  数据来源: QQ音乐 148首 | 网易云 236首
  流派: mandopop 45% | pop 25% | r&b 12% | rock 8%
  Top 艺术家: 周深、周杰伦、邓紫棋、林俊杰、薛之谦
```

---

## Step 3: 规划播放列表

**在生成前询问用户主题/场景**（这是唯一的交互步骤）

如果主题已在调用中提供（如"生成深夜放松歌单"），直接使用。
否则询问：

```
你想要什么主题的播放列表？这里有一些建议：

- "深夜放松" — 舒缓慢歌
- "通勤路上" — 活力节拍
- "雨天心情" — 忧郁温馨
- "运动燃脂" — 高能电子/摇滚
- "随机惊喜" — 根据你的品味随机

或者告诉我你的想法！
```

确定播放列表参数：
- **主题/情绪** — 用户输入，或默认为画像中的 Top 情绪
- **歌曲数量** — 用户输入，默认 5 首
- **流派混合** — 根据画像加权，增加多样性

### 歌词语言规则

| 流派 | 歌词语言 |
|------|---------|
| 华语流行/中国风/民谣 | 中文 |
| K-pop / 韩式 R&B | 韩文 |
| J-pop / City Pop / J-Rock | 日文 |
| 西方流行/摇滚/爵士/R&B | 英文 |
| 纯音乐/Lo-fi/Ambient | 无歌词 (`--instrumental`) |

**在 mmx prompt 中自然嵌入语言：**
- ✅ 好: `"A melancholy Chinese R&B ballad with gentle male voice, electric piano, slow tempo"`
- ❌ 差: `"R&B ballad, melancholic... sung in Chinese"`

### 展示播放列表计划

```
播放列表计划：深夜放松（5首）

1. 华语 R&B — 抒情  中文/男声
   温暖男中音，电子钢琴，舒缓贝斯，慢速节奏

2. Lo-fi Hip-hop — 梦幻  纯音乐
   梦幻 Lo-fi，采样钢琴，黑胶噪音，轻柔电子鼓

3. 华语民谣 — 治愈  中文/女声
   清澈女声，木吉他，口琴，安静独处

4. 轻爵士 — 浪漫  英文/女声
   丝滑女声，萨克斯，钢琴，浪漫星空

5. Ambient — 平静  纯音乐
   柔和合成器琶音，梦幻氛围
```

展示后直接开始生成，无需确认。

---

## Step 4: 生成歌曲

使用 `mmx music generate` **串行生成**所有歌曲。

> ⚠️ **重要：mmx CLI 不支持并行执行**
> 测试发现 `& + wait` 后台并行会导致超时或失败，可能因为 MiniMax API 有并发限制。
> 必须使用串行方式逐首生成。

```bash
# 串行生成（必须）
mmx music generate --prompt "<英文prompt_1>" --lyrics-optimizer \
  --out /opt/data/Music/playlists/<name>/01_desc.mp3 --quiet --non-interactive
mmx music generate --prompt "<英文prompt_2>" --instrumental \
  --out /opt/data/Music/playlists/<name>/02_desc.mp3 --quiet --non-interactive
```

**关键参数：**
- `--lyrics-optimizer` — 自动生成歌词（人声曲目）
- `--instrumental` — 无歌词纯音乐
- `--vocals "<描述>"` — 人声风格
- `--genre`, `--mood`, `--tempo`, `--instruments` — 精细控制
- `--quiet --non-interactive` — 批量模式静默输出
- `--out <路径>` — 保存路径

**文件命名：** `<NN>_<简短描述>.mp3`（如 `01_rnb_midnight.mp3`）

**输出目录：** `/opt/data/Music/playlists/<播放列表名称>/`

**失败重试：** 单首失败时重试一次，记录错误并继续。

---

## Step 5: 播放

检测可用播放器并按顺序播放：

| 播放器 | 命令 | 控制 |
|--------|------|------|
| mpv | `mpv --no-video <file>` | `q` 跳过，Space 暂停 |
| ffplay | `ffplay -nodisp -autoexit <file>` | `q` 跳过 |
| afplay | `afplay <file>` | Ctrl+C 跳过 |

按文件名顺序播放目录中的所有 `.mp3` 文件。
仅播放本次会话生成的歌曲，如有旧文件先清理或过滤。

无播放器时仅显示文件路径。

---

## 🔄 重新播放历史播放列表

如用户要求播放之前的列表：
```
ls /opt/data/Music/playlists/
```
展示可用列表，播放选中的。

---

## ⚠️ 注意事项

1. **歌单必须公开** — 私密歌单无法解析
2. **QQ音乐 Referer 必须带** — 否则返回空数据
3. **汽水音乐需浏览器** — Docker 环境需配置 Playwright
4. **所有 mmx prompt 用英文** — 生成质量最佳
5. **歌词语言按流派** — 非用户 UI 语言

---

## 🔧 技术说明

### 文件结构

```
minimax-music-playlist-cn/
├── SKILL.md                    # 本文档
├── playlist_parser.py          # 解析器（纯标准库）
└── data/
    └── artist_genre_map.json   # 23,000+ 艺术家流派映射
```

### 与官方版的关系

本 skill 基于 `minimax-music-playlist v2.0` 官方版优化：
- ✅ 保留：5 步工作流、流派映射表
- ✅ 新增：QQ音乐/网易云/汽水音乐在线解析
- ✅ 调整：数据源优先级改为在线链接优先
- ✅ 调整：生成方式改为串行（mmx 不支持并行）
- ✅ 简化：纯 Python 标准库，无外部依赖
- ❌ 移除：Spotify 数据导出流程
- ❌ 移除：Apple Music osascript（CN 用户少）
- ❌ 移除：MusicBrainz API（官方也未实现）
- ❌ 移除：反馈机制（后续按需添加）
- ❌ 移除：并行生成（mmx CLI 不支持）
- ❌ 移除：专辑封面生成（简化流程）
- ❌ 移除：playlist.json 保存（简化流程）
