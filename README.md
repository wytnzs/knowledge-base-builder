# knowledge-base-builder · 知识库原技能 · 基座

> 帮一个人从零建起自己的知识库，并在建库当天用一件真事跑通第一条工作回路。
> 交出去的是一层基座——结构、规则、跨 Agent 的读法、工作回路、体检、版本——模块和内容管线长在上面。

## 这是什么

不是模板，是基座。先访谈定定位，再按 `00–05` 六个角色搭骨架，把规则、Agent 适配、工作回路、体检和版本一起交付；日常动作拆成八个可安装模块。

**判断标准**：换一个人、换一个职业、换一个 Agent，长出来的是他自己的库，而且他真用得上。

## 核心：不是建好，是用上

三条同时成立才算交付：

1. 他手里有一个能用的库；
2. 建库当天，用一件真事跑通一条工作回路，产出一个能直接用的东西；
3. 下周同一件事，他会自己回到库里取，并写回至少一样东西。

只满足第一条 = 没做完。

## 三层

| 层 | 谁负责 | 管什么 |
|---|---|---|
| 基座层 | 本 skill | 六个角色、五个根文件、读写协议、工作回路、体检、版本 |
| 模块层 | `modules/` 八个子 skill | 收件、铸卡、项目、复盘、体检等日常动作 |
| 内容层 | 各自的管线 skill | 写作、选题、手册、客户；只读基座 |

接口、版本和升级规则见 `references/基座契约.md`。

## 五个根文件

| 文件 | 给谁看 | 管什么 |
|---|---|---|
| `README.md` | 人 | 这个库干什么、每个区放什么、怎么用 |
| `AGENTS.md` | 所有 Agent | 规则正文：启动顺序、角色、硬规则、路由、禁止 |
| `CLAUDE.md` / `AI协作规则.md` | 具体 Agent | 只做入口，指向 `AGENTS.md` |
| `.kb-base.json` | 程序 | 角色映射、Agent、版本、契约、已装模块、回路 |
| `写入规则.md` | 人和 Agent | 东西从哪进、什么时候建卡、什么不建 |
| `工作回路.md` | 人和 Agent | 用上的路径：触发、读什么、产出什么、写回什么 |
| `采用记录.md` | 人 | 每跑一次记一行 |

## 跨 Agent

先问用户用哪个 AI，再决定写哪个规则文件、模块装哪里：

| Agent | 规则文件 | 模块装哪 |
|---|---|---|
| Claude Code | `CLAUDE.md`（导入 `AGENTS.md`） | `.claude/skills/` |
| Codex | `AGENTS.md` | `skills/` |
| WorkBuddy | `AGENTS.md` + `开场卡.md` | `操作模块/<模块>.md` |
| 通用网页 / App | `AI协作规则.md` + `开场卡.md` | 无，贴开场卡 |

**不要写死 `CLAUDE.md`。** 规则正文永远是 `AGENTS.md`。

## 安装

通用 skills 安装：

```bash
npx skills add wytnzs/knowledge-base-builder
```

Claude Code 项目内安装：

```bash
git clone https://github.com/wytnzs/knowledge-base-builder.git ".claude/skills/knowledge-base-builder"
```

或把整个目录放到项目的 `.claude/skills/knowledge-base-builder/`。WorkBuddy 用户把整个目录发给它，或直接用 `templates/开场卡.md`。

## 你可以直接这样说

- 「我想建个知识库，但我不知道从哪下手。」
- 「我建了知识库，但平时根本想不起来用。」
- 「我主要用 WorkBuddy，不用 Claude Code，这套能用吗？」
- 「我的库建了半年，东西不少，但每次干活还是从头找。」

## 用法

对 Agent 说一句：

> 我想建个知识库。

它会先问三件事：手上有什么材料、最想让它干成哪件事、每周/每次重复做的那件事是什么。
四轮建库 + 第五轮跑第一条工作回路，产出一个真东西。

已有库想补基座：

> 我这个库建了半年，没怎么用起来。

它会走采用诊断：选一条回路，准备真材料跑到跑通，查断点。

## 可选：微信 / 朋友圈

微信是「了解你」的可选来源，先问同意，不同意就跳过。

```bash
# 探测本机能力（不读正文）
python scripts/wechat_probe.py

# 看安装方案，不执行
python scripts/wechat_install.py --method wechat-cli-moments --dry-run

# 同意后执行
python scripts/wechat_install.py --method wechat-cli-moments --yes
wechat-cli init
wechat-cli moments feed --limit 20
```

`wechat-cli` 负责聊天；本仓库的补丁给它加 `moments` 子命令，读朋友圈。Windows 已实测；macOS Apple Silicon 待实测，Intel 暂不作为承诺；Linux 未验证。详细边界见 `references/微信适配.md`。
**不放第三方二进制、不放密钥；原文进私人来源，不进 `03-Knowledge`。**

## 装模块

```bash
python .claude/skills/knowledge-base-builder/scripts/install_modules.py \
  --target "D:/我的库" --agent claude-code --modules default
```

WorkBuddy / 通用聊天：

```bash
python .claude/skills/knowledge-base-builder/scripts/install_modules.py \
  --target "D:/我的库" --agent workbuddy --modules default
```

模块登记表：`modules/manifest.json`。模块正文：`modules/<名字>/SKILL.template.md`。

## 验证

```bash
# 只验基座
python .claude/skills/knowledge-base-builder/scripts/check_kb.py \
  --root "D:/我的库" --profile base

# 验有没有真用上
python .claude/skills/knowledge-base-builder/scripts/check_kb.py \
  --root "D:/我的库" --profile use

# 第一版交付
python .claude/skills/knowledge-base-builder/scripts/check_kb.py \
  --root "D:/我的库" --profile v0
```

脚本只提示「有没有」，不判断「对不对」；内容和边界仍由人复核。

包自身校验：

```bash
python scripts/validate_skill.py .        # 包结构
python scripts/trigger_eval.py . --cases evals/trigger_cases.json
```

（`validate_skill.py` 来自 qiaomu-meta-skill，开发时用。）

## Troubleshooting（遇到问题）

| 现象 | 先查 |
|---|---|
| Agent 读不到规则 | 用的是哪个 Agent？规则正文在 `AGENTS.md`，入口文件是否对应 |
| 模块装了但不触发 | 是不是清单模式？WorkBuddy/通用聊天要把 `操作模块/<模块>.md` 发给它 |
| 库建了但用不上 | 跑 `--profile use`，看 `采用记录.md` 有没有行；再查 `工作回路.md` 的断点表 |
| 占位符没替换 | 重装模块；`grep "{{"` 有残留就是没装好 |
| `.kb-base.json` 读不了 | 先修 JSON，别覆盖；两个脚本都会拒绝覆盖坏文件 |
| 目录名和默认不一样 | `--inbox --projects ...` 传实际目录名，或直接改 `.kb-base.json` |

## 包内结构

```text
knowledge-base-builder/
├── SKILL.md                 主 skill：建 / 长 / 修 / 用
├── references/              基座契约、工作回路、Agent 适配、微信适配、对话样例、理念、访谈、流程、运转、架构、路由、模块安装
├── templates/               骨架（含 AGENTS.md、CLAUDE.md、工作回路、采用记录、开场卡、现状扫描、工作数据技能表、私人来源清单、kb-base.json）
├── modules/                 8 个日常模块（SKILL.template.md）+ manifest.json 登记表
├── scripts/                 check_kb.py、install_modules.py、discover_person.py、wechat_probe.py、wechat_install.py
├── tools/wechat/            wechat-cli Moments 补丁（不放二进制）
├── evals/                   触发测试、场景、输出验收、验收清单
├── agents/interface.yaml    跨 Agent 接口
├── manifest.json            版本与变更记录
└── reports/                 Skill IR、触发评估、干跑与交付记录
```

## 版本

v2.1.0

## License

MIT
