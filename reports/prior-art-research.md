# Prior Art Research

- 日期：2026-11-14
- 查询：`knowledge base builder agent skill`、`personal knowledge management second brain`、`knowledge base onboarding workflow`
- 来源：SkillsMP（skillsmp.com）metadata；`skills.sh` / `npx skills find` 在本机不可用（`npx` 不在 PATH），标为 missing evidence。
- 指标口径：`repo_stars` 是 GitHub 仓库星数，不是 skill 安装量、不是用户评分，也不是单个 skill 的质量分。

## 候选

| 候选 | 来源 | 仓库星数 | 看中的机制 | 处理 |
|---|---|---:|---|---|
| `knowledge-ops` | affaan-m | 301144 | 知识库的摄入、同步、检索分层 | 采纳「摄入与判断分开」，不采纳多存储检索引擎 |
| `unified-memory` | affaan-m | 301144 | 在 Claude / Codex / Hermes / Cursor / OpenAI 之间共享可检查的上下文与交接 | 采纳「Agent 中立上下文 + 适配层」，不采纳跨工具同步运行时 |
| `feishu-wiki` | openclaw | 394354 | 先导航、再进入知识库的工作流 | 采纳「读协议 + 角色映射」，不绑定飞书 |
| `brand-discovery` | affaan-m | 301144 | 可恢复的多轮结构化访谈 | 采纳「一次一步 + 进度文件 + 下次从哪继续」，不照搬八模块问卷 |
| `docs-governance` | affaan-m | 301144 | 文档治理路由 | 仅参考路由写法，不纳入核心 |
| `project-graveyard` | Shubhamsaboo | 144460 | 扫描废弃项目 | 与建库无关，拒绝 |

## Keep / Adapt / Reject / Invent

**Keep（自有，继续保留）**

- 六个角色、唯一入口、领域管长期/项目管短期；
- 判断卡四要素、候选区、本人签署；
- 先访谈再共建，不套模板；不删不覆盖不迁存量。

**Adapt（借机制，不照搬）**

- `knowledge-ops`：把「外部数据摄入」和「判断沉淀」分成两层。本包落成：来源只读、`03-Knowledge` 唯一正文、外部数据走 `data-warehouse`。
- `unified-memory`：把跨 Agent 的上下文做成可检查的文件，而不是某个平台的会话记忆。本包落成：`AGENTS.md` 规则正文 + `CLAUDE.md` / `AI协作规则.md` 适配入口 + `.kb-base.json` 机器状态。
- `feishu-wiki`：知识库先解决「怎么找到」，再解决「存什么」。本包落成：读协议（先 `AGENTS.md` 和 `05-Me`，再工作回路，再任务层）。
- `brand-discovery`：多轮访谈要可恢复。本包落成：`建库进度.md` 记录走到哪、下次从哪开始；一次只推进一步。

**Reject（明确不学）**

- 重图/向量 RAG、自动摄入流水线：超出「个人建库」的范围，会把轻库做成工程。
- 跨工具同步运行时：本包只生成可读文件，不做同步服务。
- 品牌/人设生成：不是这个 skill 的职责。
- 平台绑定：不为飞书、Obsidian、Notion 等任何一家写死接口。

**Invent（本包自己的）**

- **工作回路**：把「用上」做成可执行单位——触发 / 读什么 / 产出什么 / 写回什么。
- **建库当天跑第一条回路**：第五轮，不等到以后。
- **采用记录 + 用真材料跑到跑通**：用一行一行的事实判断有没有真用上，不靠感觉。
- **五个根文件 + Agent 适配矩阵**：规则正文一份，入口按 Agent 生成；模块分 skills / checklists 两种装法。
- **`--profile use`**：体检不只看结构，还看采用。

## 证据缺口

- `skills.sh` 未查询（`npx` 不可用）；只有 SkillsMP 单一目录来源。
- 没有下载或执行候选 skill 的源码，只读目录 metadata；候选内部质量未核。
- 没有用户评分、安装量或真实采用数据。
- 按次采用协议的有效性尚未用真实用户验证，标为 hypothesis。
