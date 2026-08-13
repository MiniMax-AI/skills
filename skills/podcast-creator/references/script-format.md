# Podcast Script Format

The podcast-creator skill accepts scripts in three formats.

## Format 1: Plain Text

Separate segments with blank lines. The first line becomes the title.

```
My Podcast Episode

Welcome to the show. Today we talk about AI-generated audio content.

The main topic is how text-to-speech and music generation APIs
can work together to produce complete podcast episodes.

Thanks for listening. See you next time.
```

## Format 2: Markdown

Use headings as chapter markers.

```markdown
# My Podcast Episode

## Introduction
Welcome to the show. Today we talk about AI-generated audio content.

## Main Topic
The main topic is how text-to-speech and music generation APIs
can work together to produce complete podcast episodes.

## Wrap-up
Thanks for listening. See you next time.
```

## Format 3: Structured JSON

Full control over chapters, voice, and music style.

```json
{
  "title": "My Podcast Episode",
  "voice_id": "male-qn-qingse",
  "music_style": "Lo-fi beats, relaxed, warm",
  "chapters": [
    {
      "type": "intro",
      "title": "Introduction",
      "text": "Welcome to the show. Today we talk about AI-generated audio content."
    },
    {
      "type": "segment",
      "title": "Main Topic",
      "text": "The main topic is how text-to-speech and music generation APIs can work together to produce complete podcast episodes."
    },
    {
      "type": "outro",
      "title": "Wrap-up",
      "text": "Thanks for listening. See you next time."
    }
  ]
}
```

### Chapter types

| Type | Description |
|------|-------------|
| `intro` | Opening segment. Narrated over intro music fade. |
| `segment` | Main content chapter. |
| `outro` | Closing segment. Fades into outro music. |

### Optional fields

| Field | Default | Description |
|-------|---------|-------------|
| `voice_id` | `male-qn-qingse` | MiniMax voice ID for narration |
| `music_style` | `"Ambient, professional, modern"` | Prompt for music generation |
| `speed` | `0.95` | Narration speed (0.5-2.0) |
