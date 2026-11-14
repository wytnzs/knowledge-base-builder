---
title: Agent 适配
type: reference
description: 同一个知识库怎么在 Claude Code、Codex、WorkBuddy 和通用聊天里用起来——规则文件、模块装法、降级方案
---

# Agent 适配

> 库是同一个库，Agent 不是一个 Agent。
> 不要写死 `CLAUDE.md`：先问他用哪个，再决定写哪个文件、模块装哪里、装不了怎么降级。

## 一、先问一句

> 你平时用哪个 AI 干活？Claude Code、Codex、WorkBuddy，还是直接在网页 / App 里聊？

答案决定三件事：

| 项 | 看什么 |
|---|---|
| 规则文件 | 这个 Agent 开工前读哪个文件 |
| 模块装法 | 它支不支持项目级 skill 目录 |
| 降级方案 | 不支持时，怎么让它照样按步骤做 |

## 二、适配表

| Agent | 规则文件 | 模块装哪 | 降级 |
|---|---|---|---|
| Claude Code | `CLAUDE.md`（导入 `AGENTS.md`） | `.claude/skills/<模块>/SKILL.md` | 直接把模块内容当清单贴进对话 |
| Codex | `AGENTS.md` | `skills/<模块>/SKILL.md`，或只给清单 | 读 `AGENTS.md` + `操作模块/` |
| WorkBuddy | `AGENTS.md` + `开场卡.md` | 不支持 skill 目录 → `操作模块/<模块>.md` | 把开场卡和模块清单发给它 |
| 通用网页 / App | `AI协作规则.md` + `开场卡.md` | 无 | 每次贴开场卡 + 当前任务 |

**规则正文只有一份**：`AGENTS.md`。其他文件只做入口或适配，不复制判断。

## 三、根文件在不同 Agent 里叫什么

| 角色 | 文件名 | 说明 |
|---|---|---|
| 人看 | `README.md` | 所有 Agent 通用 |
| Agent 看 | `AGENTS.md`（正文）；`CLAUDE.md`（Claude Code 入口）；`AI协作规则.md`（通用入口） | 后两个指向 `AGENTS.md` |
| 程序看 | `.kb-base.json` | 所有 Agent 通用 |
| 规则 | `写入规则.md` | 所有 Agent 通用 |
| 用上 | `工作回路.md` | 所有 Agent 通用 |

`CLAUDE.md` 里不重写规则，只写：

```markdown
@AGENTS.md

# Claude Code 补充
- 本项目 skills 在 `.claude/skills/`
- 工作回路见 `工作回路.md`
```

Claude Code 支持 `@` 导入；不支持导入的版本，就把 `AGENTS.md` 内容原样复制过来，并在文件头写「正文以 AGENTS.md 为准」。

## 四、模块的两种装法

### 4.1 原生 skill（Claude Code / Codex）

装到 Agent 认的 skill 目录，占位符换成实际路径。用户说「用收件模块」，Agent 自动找到。

### 4.2 清单模式（WorkBuddy / 通用聊天）

没有 skill 目录，就把模块写成 `操作模块/<模块名>.md`：

```text
模块：收件分流
什么时候用：入口积压、不知道放哪
步骤：1... 2... 3...
做完检查：...
下一步：只建议，不自动做
```

用户把文件发给 Agent，或直接说「按收件模块做」。效果一样，只是不自动触发。

**装不了模块，不等于基座不能用。** 五个根文件在任何 Agent 里都成立。

## 五、开场卡

通用 Agent 没有项目上下文，每次都要重新认识他。给一张一屏的开场卡：

```text
你是我的知识库助手。先读这几份：
- AGENTS.md：规则和边界
- 05-Me/我是谁.md：我是谁、按什么标准
- 工作回路.md：我现在要做的是哪条回路
- 写入规则.md：东西放哪

这次要做：<回路名>。
产出：<交付物>。
做完写回：<写回位置>。
不确定的先问我，不要编。
```

开场卡由 P9 生成，放在根目录，文件名 `开场卡.md`。

## 六、不许做的事

- 不写死 `CLAUDE.md`：他不用 Claude Code，这个文件就是废纸；
- 不在多个规则文件里写不同版本的规则；
- 不假设所有 Agent 都能装 skill；
- 不把「装不上模块」说成「基座没建好」。
