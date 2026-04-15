---
name: minimax-text-gen
description: >
  Integrate MiniMax's text generation API (chat completions) into Python or JavaScript
  applications. Use when the user wants to add MiniMax LLM support to their code, call
  the chat completion API directly, generate text programmatically, build chatbots, or
  use MiniMax-M2.7 or MiniMax-M2.7-highspeed models in their application. Also triggers
  for: "how to use MiniMax API in Python/JS", "MiniMax chat completion", "add MiniMax
  to my project", "integrate MiniMax LLM", "call MiniMax API", "MiniMax OpenAI-compatible".
  Do NOT use for: music generation (use minimax-music-gen), image/video generation
  (use minimax-multimodal-toolkit), or PDF/document creation.
license: MIT
metadata:
  version: "1.0"
  category: ai
  sources:
    - https://platform.minimax.io/docs/api-reference/text-openai-api
---

# MiniMax Text Generation

Integrate MiniMax's chat completion API into your application using the OpenAI-compatible
interface. Supports streaming, function calling, and system prompts.

## Models

| Model | Use Case |
|---|---|
| `MiniMax-M2.7` | Best quality — peak performance, complex tasks |
| `MiniMax-M2.7-highspeed` | Same capability, faster response, lower latency |

## Prerequisites

**API Key** — set in your environment:

```bash
export MINIMAX_API_KEY="your-key-here"
```

Get your API key from [MiniMax Platform](https://platform.minimaxi.com/).

**API Constraints:**
- `temperature`: range `(0.0, 1.0]` — **cannot be 0**, default `1.0`
- `response_format` with `json_object`: not supported — use prompt-guided JSON instead
- Base URL: `https://api.minimax.io/v1` (global)

---

## Python

### Install

```bash
pip install openai
```

### Basic Chat Completion

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["MINIMAX_API_KEY"],
    base_url="https://api.minimax.io/v1",
)

response = client.chat.completions.create(
    model="MiniMax-M2.7",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello! What can you do?"},
    ],
    temperature=1.0,
    max_tokens=1024,
)

print(response.choices[0].message.content)
```

### Streaming

```python
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["MINIMAX_API_KEY"],
    base_url="https://api.minimax.io/v1",
)

stream = client.chat.completions.create(
    model="MiniMax-M2.7",
    messages=[{"role": "user", "content": "Write a short poem about AI."}],
    temperature=1.0,
    stream=True,
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
print()
```

### Function Calling

```python
import json
import os
from openai import OpenAI

client = OpenAI(
    api_key=os.environ["MINIMAX_API_KEY"],
    base_url="https://api.minimax.io/v1",
)

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a location",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {"type": "string", "description": "City name"},
                    "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                },
                "required": ["location"],
            },
        },
    }
]

response = client.chat.completions.create(
    model="MiniMax-M2.7",
    messages=[{"role": "user", "content": "What's the weather in Tokyo?"}],
    tools=tools,
    tool_choice="auto",
    temperature=1.0,
)

msg = response.choices[0].message
if msg.tool_calls:
    call = msg.tool_calls[0]
    args = json.loads(call.function.arguments)
    print(f"Function: {call.function.name}, Args: {args}")
```

### Using the High-Speed Model

```python
response = client.chat.completions.create(
    model="MiniMax-M2.7-highspeed",  # faster, same quality
    messages=[{"role": "user", "content": "Summarize this in one sentence: ..."}],
    temperature=1.0,
    max_tokens=256,
)
```

---

## JavaScript / TypeScript

### Install

```bash
npm install openai
```

### Basic Chat Completion

```typescript
import OpenAI from "openai";

const client = new OpenAI({
  apiKey: process.env.MINIMAX_API_KEY,
  baseURL: "https://api.minimax.io/v1",
});

const response = await client.chat.completions.create({
  model: "MiniMax-M2.7",
  messages: [
    { role: "system", content: "You are a helpful assistant." },
    { role: "user", content: "Hello! What can you do?" },
  ],
  temperature: 1.0,
  max_tokens: 1024,
});

console.log(response.choices[0].message.content);
```

### Streaming

```typescript
const stream = await client.chat.completions.create({
  model: "MiniMax-M2.7",
  messages: [{ role: "user", content: "Write a haiku about the ocean." }],
  temperature: 1.0,
  stream: true,
});

for await (const chunk of stream) {
  process.stdout.write(chunk.choices[0]?.delta?.content ?? "");
}
console.log();
```

---

## Direct HTTP (curl / fetch)

```bash
curl https://api.minimax.io/v1/chat/completions \
  -H "Authorization: Bearer $MINIMAX_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "MiniMax-M2.7",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 1.0
  }'
```

---

## Integration Checklist

When adding MiniMax text generation to a project:

- [ ] Set `MINIMAX_API_KEY` in environment (`.env`, secrets manager, or shell)
- [ ] Use base URL `https://api.minimax.io/v1`
- [ ] Set `temperature` to `1.0` (cannot be `0`)
- [ ] Choose model: `MiniMax-M2.7` (quality) or `MiniMax-M2.7-highspeed` (speed)
- [ ] If user needs JSON output: guide via system prompt, not `response_format`
- [ ] For multi-turn chat: include full message history in `messages` array

## Troubleshooting

| Problem | Solution |
|---|---|
| `401 Unauthorized` | Check `MINIMAX_API_KEY` is set and valid |
| `invalid temperature` | Use `temperature > 0.0`, e.g. `1.0` |
| Empty response | Check `max_tokens` is sufficient |
| Slow response | Switch to `MiniMax-M2.7-highspeed` |
| JSON not returned | Remove `response_format`, use system prompt: "Respond in JSON only" |
