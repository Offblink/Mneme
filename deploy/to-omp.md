# 部署到 Oh My Pi (omp)

## 前提

- 已安装 omp
- 工作目录已知（通常是你的项目根目录）

## 步骤

### 1. 启用记忆后端

在 `~/.omp/agent/config.yml` 中添加：

```yaml
memory:
  backend: local
```

### 2. 找到记忆路径

`memory://root` 在 omp 中解析为 `~/.omp/agent/memories/<项目标识>/`。

项目标识是工作目录路径的编码形式。例如 `C:/tmp` → `--C--tmp--`。

### 3. 部署记忆文件

```bash
cp MEMORY.md ~/.omp/agent/memories/<项目标识>/MEMORY.md
cp memory_summary.md ~/.omp/agent/memories/<项目标识>/memory_summary.md
```

### 4. 部署 skill（可选，给其他 agent 用）

```bash
mkdir -p ~/.omp/skills/mneme
cp skills/mneme/SKILL.md ~/.omp/skills/mneme/SKILL.md
```

### 5. 重启 omp

下一次会话启动时，记忆管道会处理这些文件。`memory_summary.md` 会被注入到系统 prompt 中。

## 注意事项

- omp 的记忆管道（local backend）会在启动时从会话记录中重新生成操作知识。手动写入的 `MEMORY.md` 可能被覆盖。建议将 `MEMORY.md` 备份在项目仓库中。
- `内在成长` 部分是固定内容，应确保记忆管道保留或手动恢复它。
- 如果使用 `retain` 工具，记忆会通过 `mnemopi` 或 `hindsight` 后端以更结构化的方式存储。
