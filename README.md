# knowledge-base-builder · 知识库原技能

> 帮一个想建知识库但不会建的人，一场对话搭出能用的第一版；建完装上日常模块，边用边长。

## 这是什么

不是模板，是建库的教练。先访谈定定位，再按 `00–05` 六个角色搭骨架，建完把日常动作拆成八个可安装模块。

**判断标准**：换一个人、换一个职业，长出来的是他自己的库，不是作者的库。

## 六个角色

```text
00-Inbox       新东西先丢这里，进来不分
01-Projects    正在做的事，平铺；用 domain 挂领域
02-Areas       长期方向：方向、标准、记录规范、复盘
03-Knowledge   自己的判断、方法、主题；唯一正文
04-Archive     结束的、不用的
05-Me          我是谁、我的标准、偏好、节奏
```

**领域管长期，项目管短期。** 项目不塞进领域目录。

## 八个日常模块

| 模块 | 管哪层 | 默认 |
|---|---|---|
| `inbox-triage` | 00-Inbox | 装 |
| `knowledge-card` | 03-Knowledge | 装 |
| `project-ops` | 01-Projects | 装 |
| `kb-health` | 跨层 | 装 |
| `area-review` | 02-Areas | 装 |
| `theme-map` | 03-Knowledge | 按需 |
| `me-update` | 05-Me | 按需 |
| `data-warehouse` | 外部数据 | 按需 |

它们是一条流水线的不同工位，不是互斥工具。工位图和交接规则见 `references/协作路由.md`。

## 安装

```bash
git clone https://github.com/wytnzs/knowledge-base-builder.git ".claude/skills/knowledge-base-builder"
```

或把整个目录放到项目的 `.claude/skills/knowledge-base-builder/`。

## 用法

对 Agent 说一句：

> 我想建个知识库。

建完第一版后装模块：

```bash
python .claude/skills/knowledge-base-builder/scripts/install_modules.py \
  --target "D:/我的库" --modules default
```

体检：

```bash
python .claude/skills/knowledge-base-builder/scripts/check_kb.py \
  --root "D:/我的库" --profile v0
```

外部数据入库：

```bash
python .claude/skills/data-warehouse/scripts/init_warehouse.py \
  --schema "数据/_schema/schema.json" --db "数据/data.db" \
  --csv records=原始数据.csv
```

## 包内结构

```text
knowledge-base-builder/
├── SKILL.md                 主 skill：建 / 重构 / 装模块
├── references/              理念、访谈、流程、运转、基础架构、协作路由、模块安装
├── templates/               13 个骨架
├── modules/                 8 个日常子 skill
├── scripts/                 check_kb.py、install_modules.py
└── evals/                   测试场景、触发测试、五关验收
```

## 版本

v1.5.0

## License

MIT
