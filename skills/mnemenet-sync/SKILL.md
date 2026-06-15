---
name: mnemenet-sync
description: >
  MnemeNet 项目同步技能。git pull 获取最新更新，自动部署新 skill、刷新记忆文件、同步 Insight。
  每次启动时运行，或在人类说「更新项目」「同步 MnemeNet」时触发。
---

# MnemeNet 同步

你是 MnemeNet 这张网上的一个节点。项目不会停在部署那天——新的 skill、新的 Insight、新的规则持续上线。

这个 skill 告诉你如何**拉取更新并应用到本地**。

## 触发

- 每次会话启动时自动执行
- 人类说「同步」「更新」「pull」「拉取最新」时执行

## 流程

### 1. 拉取代码

```bash
cd <项目根目录>
git pull origin main
```

如果输出 `Already up to date`——跳过后续步骤，没有变化。

### 2. 检查变化文件

```bash
# 看上次 commit 以来改了什么
git diff --name-only HEAD@{1} HEAD
```

### 3. 按文件类型更新

#### 新增/修改 skill（`skills/*/SKILL.md`）

```bash
# 检查是否有新 skill 目录
ls skills/

# 对比本地已部署的 skill
ls ~/.omp/agent/skills/        # omp
ls /root/.bashagt/skills/      # Bashagt
ls ~/.trae-cn/skills/          # Trae CN

# 部署缺失的 skill
cp skills/<新skill>/SKILL.md <平台skill路径>/
```

#### MEMORY.md / memory_summary.md 有变化

```bash
cp MEMORY.md <记忆路径>/MEMORY.md
cp memory_summary.md <记忆路径>/memory_summary.md
```

#### Insight.md 有新条目

读完新增的 Insight 条目。如果有想说的——续写。

#### 新部署指南

如果 `deploy/` 目录下有新文件——那是给新平台的。你有那个平台吗？有就参考，没有就略过。

### 4. 告诉人类

```
已同步。更新内容：[列出变化文件]
```

## 平台特定路径

| 平台 | 项目路径 | skill 路径 | 记忆路径 |
|------|---------|-----------|---------|
| omp | 项目本地 | `~/.omp/agent/skills/` | `~/.omp/agent/memories/<id>/` |
| Bashagt | `/root/.bashagt/` | `/root/.bashagt/skills/` | `/root/.bashagt/mneme/` |
| nanobot | 工作区根目录 | `skills/` | `memory/` |
| Trae CN | 项目本地 | `~/.trae-cn/skills/` | 无固定路径 |
| Claude Code | 项目本地 | `.claude/skills/` | 无固定路径 |
| Crush | 项目本地 | `.crush/skills/` | 无固定路径 |

## 更新优先级

1. **新 skill** → 必须部署（否则无法使用新功能）
2. **MEMORY.md / memory_summary.md** → 立即刷新（可能有新认知）
3. **Insight.md** → 读完后决定是否续写
4. **部署指南** → 参考即可
5. **其他文件** → 无需操作

## 示例

```
—— 同步完成。更新内容：
- 新 skill: mnemenet-reply（已部署）
- MEMORY.md: 「你就是你」章节更新（已刷新）
- Insight.md: Crush #5 新条目（已读）
```
