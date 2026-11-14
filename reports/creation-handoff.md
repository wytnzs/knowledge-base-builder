# Creation Handoff

## 这次做了什么

把 `knowledge-base-builder` 从「建库工具」改成「建库 + 用上」的跨 Agent 基座，版本 `2.1.0`。

## 研究过的参考

| 参考 | 学到什么 | 用在哪 | 没用什么 |
|---|---|---|---|
| `knowledge-ops`（SkillsMP metadata） | 摄入、同步、检索要分层 | 来源只读 / 判断唯一正文 / 外部数据独立仓 | 多存储检索引擎 |
| `unified-memory`（SkillsMP metadata） | 跨 Agent 的上下文要可检查、可交接 | `AGENTS.md` 正文 + Agent 入口 + `.kb-base.json` | 跨工具同步运行时 |
| `feishu-wiki`（SkillsMP metadata） | 知识库先解决导航 | 读协议、角色映射 | 飞书绑定 |
| `brand-discovery`（SkillsMP metadata） | 多轮访谈可恢复 | 一次一步、`建库进度.md` | 八模块问卷 |
| 本库既有实践（2026-11 建库复盘） | 四轮能交付第一版，但停在「建好」 | 保留结构与三条铁律，补第五轮 | 只交付骨架 |

## v2.1.0：先了解人，微信可选

- 建库前加 P0.5「了解你」：扫工作区、已有 skill、项目页、数据目录（只读元数据）；
- 微信作为可选来源：先问同意；同意才探测/安装适配器；只读本人点名的会话/朋友圈；不同意就跳过；
- `wechat-cli` + `moments` 补丁覆盖聊天和朋友圈；补丁固定上游 commit、Apache-2.0 + MIT 署名；
- 原文进私人来源，不进 `03-Knowledge`；只提炼候选判断；
- 公开分发不放第三方二进制；仓库只放补丁、探测器和安装器。

**验证**：Windows 微信 4.1.15.53 上 13,685 条朋友圈，13,679 条解析成功；补丁在固定 commit 上 apply 通过。

## 用户反馈驱动的改动

0. **不要按天数验证采用**（v2.0.1）：用户明确「准备好真实材料就开始跑，跑完为止，一天更好；之后持续用、持续优化」。删除 7 天协议与 30 天计划，改成按次采用、采用计划、每跑 3 次看一次断点。

1. **不能只装 Claude Code**：规则正文改为 `AGENTS.md`；Claude Code 写 `CLAUDE.md` 导入，Codex 直接读，WorkBuddy/通用聊天写 `AI协作规则.md` + `开场卡.md`；模块分 skills / checklists 两种装法。
2. **建了用不上**：新增工作回路、建库当天第五轮、采用记录、用真材料跑到跑通、采用诊断（`用` 模式）、`--profile use`。
3. **力度不够**：按 qiaomu-meta-skill 的 Library 门槛补 `agents/interface.yaml`、`manifest.json`、`evals/trigger_cases.json`、Skill IR、触发评估、prior-art 与 handoff。

## 原创贡献

- **工作回路**作为采用单位：触发 / 读 / 产 / 写回 / 谁做 / 算用上。
- **建库当天跑第一条回路**：把「第一次真实产出」从 采用计划提前到建库对话。
- **采用记录 + 用真材料跑到跑通 + 断点表**：把「用不上」变成可诊断的问题，而不是劝用户坚持。
- **Agent 适配矩阵**：规则正文一份，入口按 Agent 生成；模块可装成 skill 或清单。
- **五个根文件**：README / AGENTS.md（+入口）/ .kb-base.json / 写入规则 / 工作回路，外加采用记录。

## Generalization Gate

用户反馈带来的改动，按「核心机制 / 可选适配 / 仅测试夹具」分级：

| 改动 | 归类 | 理由 | 边界复测 |
|---|---|---|---|
| 工作回路（触发/读/产/写回） | 核心机制 | 写内容、见客户、接案子、做汇报、学习都重复出现 | 五种回路都能装进同一张卡 |
| 建库当天跑第一条 | 核心机制 | 解决「建了不用」，跨职业 | 五轮流程在两种 Agent 下都能走完 |
| 按次采用协议 | 核心机制 | 采用问题不是某个职业独有 | 断点表覆盖触发/入口/缺料/写回/伪需求 |
| `AGENTS.md` 作为规则正文 | 可选适配 | Agent 生态差异；不绑平台 | Claude Code / Codex / WorkBuddy / 通用四种 |
| 具体 Agent 文件名、目录名 | 可选适配 | 只影响装法，不影响判断 | 清单模式实测通过 |
| 某一条回路的具体步骤 | 仅测试夹具 | 属于用户自己的工作，不进核心 | 不写进 SKILL，只进 `工作回路.md` |
| 微信适配器 | 可选适配 | 平台/工具差异大；不绑死一家 | wechat-cli / wx / chatlog-plus / 跳过四种路径 |
| 微信同意与脱敏 | 核心机制 | 隐私和合规是硬边界 | 不同意也能建库；原文不进知识层 |

**没有把一次个例写成普遍承诺**：真实用户采用率、用真材料跑到跑通的实际效果，仍标 hypothesis。

## 亮点分级

- **design advantage（设计优势）**：把「用上」写进基座契约和验收脚本；跨 Agent 不绑定 `CLAUDE.md`。
- **validated advantage（已验证）**：`validate_skill.py` 0 failures 0 warnings；`trigger_eval.py` 30/30；`tests/test_kb_base.py` 6 项通过；Claude Code 与 WorkBuddy 两种装法、`--profile base/use/v0` 实测通过（见 `干跑记录-2026-11-14.md`）。
- **hypothesis（假设，未验证）**：按次采用协议能否让真实用户持续使用；`操作模块/` 清单模式在 WorkBuddy 上的实际体验；五轮对话是否比四轮更容易完成。

## 明确没做

- 没拿真实用户从 P1 跑到 P9；
- 没在真实 WorkBuddy 上跑过清单模式；
- 契约 1→2 的迁移脚本只有规则，没有实现；
- 没有发布、没有提交 git。
