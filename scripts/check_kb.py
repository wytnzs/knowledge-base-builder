#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
知识库体检（只读）。

用法：
    python check_kb.py --root "D:/我的知识库"
    python check_kb.py --root "D:/我的知识库" --stage 2

--stage 表示“现在走到第几阶段”，只检查这个阶段及之前该有的东西。
建库中途用 --stage，建完用默认 9。

这份脚本给的是提示，不是判决。它只看“有没有这个东西”，
看不出“这个东西对不对”。最终判断仍由人做。
"""
import argparse
import json
import os
import re
import sys
from collections import defaultdict

SKIP_DIRS = {".git", "node_modules", ".obsidian", ".claude", "__pycache__", "_eval", "templates"}
BASE_FILE = ".kb-base.json"
SUPPORTED_CONTRACT = 2

FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
FIELD_LINE = re.compile(r"^(\w[\w-]*):\s*(.*?)\s*$", re.M)


def load_base(root):
    path = os.path.join(root, BASE_FILE)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError):
        return {"_error": True}


def read_md(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()
    except OSError:
        return ""


def parse(path):
    text = read_md(path)
    m = FRONTMATTER.match(text)
    fm = m.group(1) if m else ""
    fields = {k: v.strip().strip('"').strip("'") for k, v in FIELD_LINE.findall(fm)}
    return {
        "path": path,
        "text": text,
        "type": fields.get("type", ""),
        "title": fields.get("title", ""),
        "fields": fields,
    }


def walk(root):
    docs, dirs = [], []
    for base, subdirs, files in os.walk(root):
        subdirs[:] = [d for d in subdirs if d not in SKIP_DIRS]
        rel = os.path.relpath(base, root)
        if rel != ".":
            dirs.append(rel)
        for name in files:
            if name.lower().endswith(".md"):
                docs.append(parse(os.path.join(base, name)))
    return docs, dirs


def has_dir_like(root, names):
    for entry in os.listdir(root):
        full = os.path.join(root, entry)
        if os.path.isdir(full) and any(k in entry.lower() for k in names):
            return entry
    return None


def count(docs, t):
    return sum(1 for d in docs if d["type"] == t)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True)
    ap.add_argument("--stage", type=int, default=9, help="当前走到第几阶段（0-9），只看这阶段之前该有的")
    ap.add_argument("--inbox", help="入口目录名；不填就从写入规则里认，再认不出来按常见名字找")
    ap.add_argument("--profile", choices=["base", "use", "v0", "full"], default="full",
                    help="base 只看基座契约；use 看有没有真用上；v0 看一场对话该交付的东西；full 看完整库")
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"找不到目录：{root}")
        return 2

    docs, dirs = walk(root)
    base = load_base(root)
    roles = (base or {}).get("roles") or {}
    top = [d for d in os.listdir(root) if os.path.isdir(os.path.join(root, d)) and d not in SKIP_DIRS]
    empty = []
    for d in dirs:
        full = os.path.join(root, d)
        try:
            if not any(files for _, _, files in os.walk(full)):
                empty.append(d)
        except OSError:
            pass

    checks = []

    def add(name, ok, detail, fix="", phase=0):
        checks.append({"name": name, "ok": ok, "detail": detail, "fix": fix, "phase": phase})

    readme = [d for d in docs if os.path.basename(d["path"]).lower() == "readme.md"]
    add("说明书 README", bool(readme), f"{len(readme)} 份" if readme else "没有",
        "在根目录写一份 README：这个库干什么、每个区放什么", 9)

    inbox = args.inbox or roles.get("inbox")
    if inbox and not os.path.isdir(os.path.join(root, inbox)):
        inbox = None
    if not inbox:
        # 先从写入规则的反引号路径里认
        for d in docs:
            if d["type"] == "write_rules" or "写入" in os.path.basename(d["path"]):
                for tok in re.findall(r"`([^`\n]+)`", d["text"]):
                    first = re.split(r"[/\\]", tok.strip().strip("/\\"))[0]
                    if first and os.path.isdir(os.path.join(root, first)):
                        inbox = first
                        break
            if inbox:
                break
    if not inbox:
        inbox = has_dir_like(root, ["inbox", "入口", "收集", "收件箱", "_in", "收件口", "新来的"])
    add("唯一入口", bool(inbox), inbox or "没识别到（入口叫别的名字就用 --inbox 指定）",
        "建一个入口目录，所有新东西先丢这里", 3)

    zone = count(docs, "zone_map") or len([d for d in docs if "职责" in os.path.basename(d["path"])])
    add("分区职责表", zone > 0, f"{zone} 份",
        "写一份分区职责表：每个区放什么、不放什么", 2)

    wr = count(docs, "write_rules") or len([d for d in docs if "写入" in os.path.basename(d["path"])])
    add("写入规则", wr > 0, f"{wr} 份",
        "写清东西从哪进、什么时候建卡、什么不建", 3)

    identity = count(docs, "identity") or len([d for d in docs if "我是谁" in os.path.basename(d["path"])])
    add("身份文件", identity > 0, f"{identity} 份",
        "写一份身份文件，AI 开工前先读", 4)

    plan = count(docs, "plan_adoption") or count(docs, "plan_30d") or len(
        [d for d in docs if "采用计划" in os.path.basename(d["path"])
         or "30天" in os.path.basename(d["path"])])
    add("采用计划", plan > 0, f"{plan} 份",
        "按跑的次数写：第一次、之后每次、每 3 次看什么；不按天数", 9)

    projects = [d for d in docs if d["type"] == "project_status"]
    no_next = [d for d in projects if not d["fields"].get("next_action")]
    add("项目状态", bool(projects), f"{len(projects)} 个，{len(no_next)} 个缺 next_action",
        "每个项目补齐：状态 / 进度 / 卡点 / 下一步", 6)

    cards = [d for d in docs if d["type"] == "knowledge_card"]
    no_source = [d for d in cards if not d["fields"].get("source")]
    add("知识卡片", bool(cards), f"{len(cards)} 张，{len(no_source)} 张缺 source",
        "每张卡补来源；没有来源的先放候选区", 5)

    themes = [d for d in docs if d["type"] == "theme_map"]
    add("主题页", True, f"{len(themes)} 张", "有多张卡指向同一个问题时才建主题页", 5)

    reviews = [d for d in docs if d["type"] == "review" or "复盘" in os.path.basename(d["path"]) or "成长" in os.path.basename(d["path"])]
    add("复盘记录", bool(reviews), f"{len(reviews)} 份",
        "复盘固定四栏：原来 / 现在 / 依据 / 影响", 7)

    bs = count(docs, "build_status") or len([d for d in docs if "进度" in os.path.basename(d["path"])])
    add("建库进度", bs > 0, f"{bs} 份",
        "写一份进度文件：走到哪、定了什么、下次从哪开始", 0)

    # ---- 基座契约 ----
    if base is None:
        add("基座契约", False, "没有 .kb-base.json",
            "用 templates/kb-base.json 生成，填角色目录、基座版本和已装模块", 3)
    elif base.get("_error"):
        add("基座契约", False, "文件在，但 JSON 读不了",
            "修好 JSON；读不了就不要覆盖", 3)
    else:
        base_roles = base.get("roles") or {}
        lack = [k for k in ("inbox", "projects", "knowledge", "me", "archive")
                if not base_roles.get(k)]
        contract = base.get("contract", "缺")
        leftover = "{{" in read_md(os.path.join(root, BASE_FILE))
        agent_cfg = base.get("agent") or {}
        rules_file = agent_cfg.get("rules") or "AGENTS.md"
        has_rules = os.path.isfile(os.path.join(root, rules_file))
        ok = (not lack and contract == SUPPORTED_CONTRACT and not leftover
              and bool(agent_cfg.get("primary")) and has_rules)
        detail = f"v{base.get('version', '?')} / 契约 {contract}"
        if agent_cfg.get("primary"):
            detail += f" / {agent_cfg.get('primary')}"
        if lack:
            detail += "；缺角色 " + "、".join(lack)
        if leftover:
            detail += "；占位符未替换"
        if not agent_cfg.get("primary"):
            detail += "；缺 agent 配置"
        if not has_rules:
            detail += f"；缺 {rules_file}"
        add("基座契约", ok, detail,
            f"替换 roles 里的占位符、补 contract；本脚本支持契约 {SUPPORTED_CONTRACT}", 3)

    if not roles:
        add("角色目录", True, "没有基座契约，跳过", "", 2)
    else:
        lack_dirs = [f"{k}={v}" for k, v in roles.items()
                     if v and not os.path.isdir(os.path.join(root, v))]
        add("角色目录", not lack_dirs,
            "、".join(lack_dirs) if lack_dirs else f"{len(roles)} 个角色目录都在",
            "按 .kb-base.json 的映射把缺的目录建出来；不建就先改映射", 2)

    rules_names = ("AGENTS.md", "CLAUDE.md", "AI协作规则.md")
    agent_rules = [d for d in docs
                   if os.path.basename(d["path"]) in rules_names
                   and os.path.dirname(os.path.relpath(d["path"], root)) in ("", ".")]
    has_order = any("启动顺序" in d["text"] for d in agent_rules)
    has_import = any("@AGENTS.md" in d["text"] for d in agent_rules)
    rules_clean = all("{{" not in d["text"] for d in agent_rules)
    detail = "、".join(os.path.basename(d["path"]) for d in agent_rules) or "没有"
    if agent_rules and not rules_clean:
        detail += "；占位符未替换"
    add("AI 协作规则", bool(agent_rules) and (has_order or has_import) and rules_clean,
        detail,
        "用 templates/AGENTS.md 写规则正文；Claude Code 再加一个 CLAUDE.md 入口", 9)

    loop_doc = [d for d in docs
                if d.get("type") == "work_loop" or os.path.basename(d["path"]) == "工作回路.md"]
    loop_ok = bool(loop_doc) and "{{" not in loop_doc[0]["text"]
    add("工作回路", loop_ok, "有" if loop_ok else ("没填完" if loop_doc else "没有"),
        "写一条真实工作回路：触发 / 读什么 / 产出什么 / 写回什么", 9)

    adopt = [d for d in docs
             if d.get("type") == "adoption_log" or os.path.basename(d["path"]) == "采用记录.md"]
    rows = 0
    if adopt:
        for line in adopt[0]["text"].splitlines():
            cell = line.strip()
            if not cell.startswith("|") or "---" in cell or "日期" in cell:
                continue
            first = cell.strip("|").split("|")[0].strip()
            if first:
                rows += 1
    add("采用记录", bool(adopt) and rows > 0,
        f"{rows} 次" if adopt else "没有",
        "每跑一次回路记一行；空表不算用上", 9)

    # 私人来源（可选）
    private_cfg = (base or {}).get("private_sources") or []
    private_dir = os.path.join(root, "私人来源")
    if private_cfg or os.path.isdir(private_dir):
        consent = [d for d in docs if d.get("type") == "private_sources"
                   or os.path.basename(d["path"]) == "私人来源清单.md"]
        knowledge_dir = os.path.abspath(os.path.join(root, roles.get("knowledge", "03-Knowledge")))
        inside = os.path.abspath(private_dir).startswith(knowledge_dir + os.sep)
        detail = f"{len(consent)} 份同意记录" if consent else "没有同意记录"
        if inside:
            detail += "；私人来源在知识层里"
        add("私人来源", bool(consent) and not inside, detail,
            "补 私人来源清单.md；原文移出知识层，只留候选判断", 9)
    else:
        add("私人来源", True, "未接", "", 9)

    installed = []
    for m in (base or {}).get("modules") or []:
        installed.append(m.get("name") if isinstance(m, dict) else m)
    installed = [m for m in installed if m]
    if not installed:
        add("模块安装", True, "还没装模块", "", 8)
    else:
        mode = ((base or {}).get("agent") or {}).get("modules_mode", "skills")
        skills_dir = ((base or {}).get("agent") or {}).get("skills_dir") or ".claude/skills"
        gone, left = [], []
        for n in installed:
            if mode == "checklists":
                main = os.path.join(root, "操作模块", f"{n}.md")
                mdir = os.path.join(root, "操作模块", n)
            else:
                main = os.path.join(root, skills_dir, n, "SKILL.md")
                mdir = os.path.join(root, skills_dir, n)
            if not os.path.isfile(main):
                gone.append(n)
                continue
            for fp in [main] + [os.path.join(b, f) for b, _, fs in os.walk(mdir) for f in fs]:
                if not fp.lower().endswith((".md", ".json", ".py", ".txt", ".yaml", ".yml")):
                    continue
                try:
                    with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                        if "{{" in fh.read():
                            left.append(os.path.relpath(fp, root))
                except OSError:
                    pass
        ok = not gone and not left
        detail = f"{len(installed)} 个"
        if gone:
            detail += "；登记了但没装：" + "、".join(gone)
        if left:
            detail += "；还有占位符：" + "、".join(left[:3])
        add("模块安装", ok, detail,
            "重装缺的模块；占位符没替换等于没装", 8)

    junk = [d for d in top if any(k in d for k in ["其他", "杂项", "待分类", "未分类", "临时"])]
    add("没有杂物区", not junk, "、".join(junk) if junk else "干净",
        "杂物区是没想清楚的地方，先把里面的东西分掉再删", 2)

    add("顶层区数量", len(top) <= 8, f"{len(top)} 个：" + "、".join(top[:10]),
        "超过 8 个先怀疑是不是按学科分", 2)

    titles = defaultdict(list)
    for d in docs:
        if d["title"]:
            titles[d["title"]].append(os.path.relpath(d["path"], root))
    dup = {k: v for k, v in titles.items() if len(v) > 1}
    add("没有重复标题", not dup, f"{len(dup)} 组重复" if dup else "没有",
        "同名文件容易漂移，合并或改名", 5)

    add("没有空目录", not empty, f"{len(empty)} 个空目录" if empty else "没有",
        "空目录先删，用到再建", 2)

    base_names = {"基座契约", "角色目录", "AI 协作规则", "工作回路", "唯一入口",
                  "写入规则", "分区职责表", "说明书 README"}
    use_names = base_names | {"采用记录", "模块安装"}
    v0_names = base_names | {"建库进度", "身份文件", "采用计划", "采用记录"}
    if args.profile == "base":
        visible = [c for c in checks if c["name"] in base_names]
        label = "基座"
    elif args.profile == "use":
        visible = [c for c in checks if c["name"] in use_names]
        label = "用上"
    elif args.profile == "v0":
        visible = [c for c in checks if c["name"] in v0_names]
        label = "第一版（一场对话）"
    else:
        visible = [c for c in checks if c["phase"] <= args.stage]
        label = f"P{args.stage}"

    print()
    print(f"知识库体检：{root}（按 {label} 看）")
    print(f"扫描到 {len(docs)} 份 Markdown，{len(top)} 个顶层目录")
    print("-" * 72)
    bad = 0
    for c in visible:
        mark = "OK  " if c["ok"] else "MISS"
        if not c["ok"]:
            bad += 1
        print(f"[{mark}] P{c['phase']} {c['name']:<10} {c['detail']}")
        if not c["ok"] and c["fix"]:
            print(f"         -> {c['fix']}")
    print("-" * 72)
    later = len(checks) - len(visible)
    if bad == 0:
        print("这一阶段该有的都齐了。")
        if later:
            print(f"还有 {later} 项属于后面的阶段，现在不用管。")
    else:
        print(f"缺 {bad} 项。一次只补最堵的那一项，别全面翻修。")
    print()
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
