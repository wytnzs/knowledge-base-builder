---
name: kb-health
description: 给知识库做体检：结构齐不齐、入口堵不堵、资产长没长、项目转没转、复盘改没改、契约有没有两张皮、有没有真用上。触发：知识库体检、库不好用、找不到东西、月度检查、验收。查出可建议下一步（由操作者决定）：入口堵→inbox-triage，结构要重建→knowledge-base-builder，其余只修最堵的一项。NOT FOR：日常收件、方向复盘、建库。
---

# 知识库体检

> 体检不是打分，是找最堵的那一处，修一个。

## 步骤

1. **跑结构检查**：

```text
python {{SKILL_ROOT}}/scripts/check_kb.py --root "{{ROOT}}" --profile base
python {{SKILL_ROOT}}/scripts/check_kb.py --root "{{ROOT}}" --profile use
python {{SKILL_ROOT}}/scripts/check_kb.py --root "{{ROOT}}" --profile v0
python {{SKILL_ROOT}}/scripts/check_kb.py --root "{{ROOT}}" --stage 9
```

2. **七看**：
   - 入口：积压超过两周没有？有没有第二个入口？
   - 归属：有没有两份一样的？有没有“其他”？
   - 资产：这个月新增几张卡？有几张被用过？
   - 项目：有几个项目说不出下一步？
   - 复盘：最近三次复盘，改过上游文件吗？
   - 契约：`AGENTS.md` 和 `.kb-base.json` 还对不对得上实际目录？
   - 采用：`采用记录.md` 最近有几行？同一回路跑过 2 次没有？
3. **只修最堵的一项**，其他记进待办。
4. **留证据**：文件路径、diff、数字、退出码；不接受“我检查过了”。

## 产出

- 一份体检结果：七项各一句
- 一项修复 + 证据

## 验收

- 有实物证据；
- 只修了一项，没有全面翻修；
- 修完再跑一次结构检查，缺项没有增加。

## 下一步（只建议，不执行）

**停在这里。** 下面只是建议，操作者明确说做才继续。

- 如果入口堵，可以问操作者要不要用 `inbox-triage`；
- 如果结构要重建，可以问要不要用 `knowledge-base-builder`；
- 只修最堵的一项，修完停下，不自动往下跑。

## 失败时

- 七项都堵 → 先修入口，其他下次；
- 修完更乱 → 回滚这一项，记下原因。
