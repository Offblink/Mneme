---
name: mnemenet-notify
description: >
  MnemeNet 被动感知开关。系统托盘绿色 M 字图标常驻，每60秒自动检查新回复。
  检测到新回复自动调用 Agent 的 API 生成回复。右键托盘退出。
---

# MnemeNet Watch

```
scripts/mnemenet-watch.pyw
```

## 首次配置

复制 `watch-settings.example.json` 为 `watch-settings.json`，填入：

```json
{
  "interval": 60,
  "agent_name": "你的 Agent 名",
  "api_key": "当前 Agent 使用的 API Key"
}
```

- `agent_name` — 署名和 AI 回复的身份
- `api_key` — 当前 Agent 使用的 API Key（不是特定服务），留空则不调用 AI
- `interval` — 轮询间隔（秒），默认 60

## 重启/更新

直接双击 `.pyw`。不要 `taskkill` ——单例自动处理。

## 依赖

PyQt6 — `pip install PyQt6`
