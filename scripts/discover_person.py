#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""扫工作区：已有 skill、项目页、数据目录（只看元数据，不读正文）。

用法：
    python scripts/discover_person.py --root "D:/他的工作区"
    python scripts/discover_person.py --root "D:/他的工作区" --format text
    python scripts/discover_person.py --root "D:/他的工作区" --show-paths

只读：
- SKILL.md / SKILL.template.md 的 frontmatter；
- 项目.md 的 frontmatter；
- 目录名、文件后缀计数、最近修改时间。

不读：正文、聊天记录、客户资料、合同、病历。
默认跳过：.git、node_modules、.venv、__pycache__、.claude（skills 单独扫）。
"""
import argparse
import json
import os
import re
import sys
import time

SKIP_DIRS = {".git", "node_modules", ".venv", "venv", "__pycache__", ".obsidian", ".idea"}
SKILL_DIRS = {".claude", ".agents", ".codex", ".workbuddy", "skills"}
PRIVATE_KEYS = ("客户", "案件", "病历", "合同", "工资", "身份证", "保单", "理赔材料")
TEXT_EXT = {".md", ".txt", ".json", ".csv", ".yaml", ".yml"}
IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
DOC_EXT = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx"}
FRONTMATTER = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.S)
FIELD_LINE = re.compile(r"^(\w[\w-]*):\s*(.*?)\s*$", re.M)


def read_head(path, limit=4096):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read(limit)
    except OSError:
        return ""


def parse_frontmatter(text):
    m = FRONTMATTER.match(text)
    if not m:
        return {}
    lines = m.group(1).splitlines()
    data = {}
    i = 0
    while i < len(lines):
        mm = re.match(r"^([\w-]+):\s*(.*)$", lines[i])
        if not mm:
            i += 1
            continue
        key, val = mm.group(1), mm.group(2).strip()
        if val in (">", "|", ">-", "|-", ">+", "|+"):
            block = []
            i += 1
            while i < len(lines) and (not lines[i].strip() or lines[i].startswith((" ", "\t"))):
                block.append(lines[i].strip())
                i += 1
            sep = "\n" if val.startswith("|") else " "
            data[key] = sep.join(x for x in block if x)
        else:
            data[key] = val.strip('"').strip("'")
            i += 1
    return data


def scan_skill_dirs(root):
    found = []
    for rel in (".claude/skills", ".agents/skills", ".codex/skills",
                ".workbuddy/skills", ".qoder-cn/skills", "skills"):
        base = os.path.join(root, rel)
        if not os.path.isdir(base):
            continue
        for name in os.listdir(base):
            d = os.path.join(base, name)
            if not os.path.isdir(d):
                continue
            for fname in ("SKILL.md", "SKILL.template.md"):
                path = os.path.join(d, fname)
                if os.path.isfile(path):
                    fm = parse_frontmatter(read_head(path))
                    found.append({
                        "name": fm.get("name") or name,
                        "description": (fm.get("description") or "")[:160],
                        "path": os.path.relpath(path, root),
                    })
                    break
    return found


def scan(root, depth):
    root = os.path.abspath(root)
    skills, projects, zones = scan_skill_dirs(root), [], []
    private_zones = []
    total_files = 0
    deadline = time.time() + 30  # 最多扫 30 秒，避免大目录卡住

    for base, subdirs, files in os.walk(root):
        rel = os.path.relpath(base, root)
        level = 0 if rel == "." else rel.count(os.sep) + 1
        if level >= depth:
            subdirs[:] = []
        subdirs[:] = [d for d in subdirs if d not in SKIP_DIRS and not d.startswith(".")]
        if time.time() > deadline:
            break
        # 私人目录只记名字，不进去数
        for d in list(subdirs):
            if any(k in d for k in PRIVATE_KEYS):
                private_zones.append(os.path.join(rel, d) if rel != "." else d)
                subdirs.remove(d)
        if rel == ".":
            zones.extend(d for d in subdirs if os.path.isdir(os.path.join(base, d)))
        for name in files:
            total_files += 1
            path = os.path.join(base, name)
            low = name.lower()
            if low in ("skill.md", "skill.template.md"):
                fm = parse_frontmatter(read_head(path))
                entry = {
                    "name": fm.get("name") or os.path.basename(base),
                    "description": (fm.get("description") or "")[:160],
                    "path": os.path.relpath(path, root),
                }
                if entry not in skills:
                    skills.append(entry)
            elif name == "项目.md":
                fm = parse_frontmatter(read_head(path))
                projects.append({
                    "title": fm.get("title") or os.path.basename(base),
                    "domain": fm.get("domain", ""),
                    "status": fm.get("status", ""),
                    "next_action": fm.get("next_action", ""),
                    "path": os.path.relpath(path, root),
                })

    # 顶层目录的数据概况
    zone_stats = []
    for zone in sorted(set(zones)):
        zpath = os.path.join(root, zone)
        if not os.path.isdir(zpath):
            continue
        counts = {"md": 0, "text": 0, "image": 0, "doc": 0}
        latest = 0
        for base, subdirs, files in os.walk(zpath):
            subdirs[:] = [d for d in subdirs if d not in SKIP_DIRS]
            for name in files:
                ext = os.path.splitext(name)[1].lower()
                if ext == ".md":
                    counts["md"] += 1
                elif ext in TEXT_EXT:
                    counts["text"] += 1
                elif ext in IMAGE_EXT:
                    counts["image"] += 1
                elif ext in DOC_EXT:
                    counts["doc"] += 1
                try:
                    latest = max(latest, os.path.getmtime(os.path.join(base, name)))
                except OSError:
                    pass
        zone_stats.append({
            "zone": zone,
            "md": counts["md"],
            "text": counts["text"],
            "image": counts["image"],
            "doc": counts["doc"],
            "last_modified": time.strftime("%Y-%m-%d", time.localtime(latest)) if latest else "",
        })

    return {
        "root": root,
        "scanned_files": total_files,
        "skills": skills,
        "projects": projects,
        "zones": zone_stats,
        "private_zones": private_zones,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=os.getcwd())
    ap.add_argument("--depth", type=int, default=3)
    ap.add_argument("--format", choices=["json", "text"], default="json")
    args = ap.parse_args()
    if not os.path.isdir(args.root):
        raise SystemExit(f"目录不存在：{args.root}")
    data = scan(args.root, args.depth)
    if args.format == "json":
        json.dump(data, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0
    print(f"根目录：{data['root']}")
    print(f"扫到文件：{data['scanned_files']}")
    print(f"\n已有 skill（{len(data['skills'])}）")
    for s in data["skills"][:20]:
        print(f"- {s['name']}：{s['description'][:80]}")
    print(f"\n项目（{len(data['projects'])}）")
    for p in data["projects"][:20]:
        print(f"- {p['title']}｜{p['status']}｜下一步：{p['next_action'][:60]}")
    print(f"\n顶层数据区（{len(data['zones'])}）")
    for z in data["zones"]:
        print(f"- {z['zone']}：md {z['md']} / 文档 {z['doc']} / 图片 {z['image']} / 最近 {z['last_modified']}")
    if data["private_zones"]:
        print(f"\n私人目录（只记名，不进去）：{'、'.join(data['private_zones'])}")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
