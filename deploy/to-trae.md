# 部署到 Trae CN

## 步骤

### 1. 找到 Trae skill 目录

`~/.trae-cn/skills/` 即 `C:\Users\<用户名>\.trae-cn\skills\`。

### 2. 部署 skill

```bash
mkdir C:\Users\<用户名>\.trae-cn\skills\mneme
copy skills\mneme\SKILL.md C:\Users\<用户名>\.trae-cn\skills\mneme\SKILL.md
```

### 3. 部署记忆文件（可选）

Trae CN 没有原生的记忆管道，但可以将 `MEMORY.md` 放在项目根目录下：

```bash
copy MEMORY.md <项目根目录>\MEMORY.md
copy memory_summary.md <项目根目录>\memory_summary.md
```

### 4. 使用

重启 Trae CN。skill 会自动被识别。在对话中 agent 可以读取 `MEMORY.md` 来获取环境知识和内在认知。

如果项目根目录有 `MEMORY.md`，告诉你的 agent：「在开始工作之前，先读取项目的 MEMORY.md」。
