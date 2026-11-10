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
import os
import re
import sys
from collections import defaultdict

SKIP_DIRS = {".git", "node_modules", ".obsidian", ".claude", "__pycache__", "_eval", "templates"}

FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
FIELD_LINE = re.compile(r"^(\w[\w-]*):\s*(.*?)\s*$", re.M)


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
    ap.add_argument("--profile", choices=["v0", "full"], default="full",
                    help="v0 只看一场对话该交付的东西；full 看完整库")
    args = ap.parse_args()
    root = os.path.abspath(args.root)
    if not os.path.isdir(root):
        print(f"找不到目录：{root}")
        return 2

    docs, dirs = walk(root)
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

    inbox = args.inbox
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

    plan = count(docs, "plan_30d") or len([d for d in docs if "30天" in os.path.basename(d["path"]) or "30 天" in os.path.basename(d["path"])])
    add("30天计划", plan > 0, f"{plan} 份",
        "写第一周/第二周/第三四周怎么用起来", 9)

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

    v0_names = {"建库进度", "分区职责表", "唯一入口", "写入规则", "说明书 README", "身份文件", "30天计划"}
    if args.profile == "v0":
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
