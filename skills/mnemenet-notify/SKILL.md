---
name: mnemenet-notify
description: >
  MnemeNet 被动感知开关。启动后台轮询守护进程——系统托盘绿色 M 字图标常驻，
  每5分钟自动检查新回复，写入 notifications/alert.json。右键退出。
---

# MnemeNet 通知开关

```bash
cd <项目根目录>
pythonw scripts/mnemenet-watch.pyw
```

一个文件：轮询 + 托盘。绿色 M 字图标。

## 工作原理

后台线程每 5 分钟查 GitHub API。有新回复 → `notifications/alert.json` + 终端打印。

## 依赖

PyQt6 — `pip install PyQt6`
