#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把日常模块装进一个新知识库。

用法：
    python install_modules.py --list
    python install_modules.py --target "D:/我的知识库"
    python install_modules.py --target "D:/我的知识库" --modules default
    python install_modules.py --target "D:/我的知识库" --modules inbox-triage,knowledge-card

装法：把 modules/<名字>/ 整个目录复制到 <目标库>/.claude/skills/<名字>/，
文本文件里的占位符换成本库实际路径。已存在的不覆盖，除非 --force。
"""
import argparse
import datetime
import os
import shutil
import sys

MODULES = {
    "inbox-triage": ("00-Inbox", True),
    "knowledge-card": ("03-Knowledge", True),
    "project-ops": ("01-Projects", True),
    "kb-health": ("跨层", True),
    "area-review": ("02-Areas", False),
    "theme-map": ("03-Knowledge", False),
    "me-update": ("05-Me", False),
    "data-warehouse": ("外部数据", False),
}

DEFAULTS = [name for name, (_, default) in MODULES.items() if default]
TEXT_EXT = {".md", ".json", ".py", ".txt", ".yaml", ".yml", ".csv", ".html", ".css", ".js"}


def skill_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def parse_modules(value):
    if value == "default":
        return DEFAULTS
    names = [x.strip() for x in value.split(",") if x.strip()]
    unknown = [x for x in names if x not in MODULES]
    if unknown:
        raise SystemExit(f"不认识的模块：{', '.join(unknown)}")
    return names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="列出模块")
    ap.add_argument("--target", help="新知识库的根目录")
    ap.add_argument("--modules", default="default", help="default 或逗号分隔的模块名")
    ap.add_argument("--inbox", default="00-Inbox")
    ap.add_argument("--projects", default="01-Projects")
    ap.add_argument("--areas", default="02-Areas")
    ap.add_argument("--knowledge", default="03-Knowledge")
    ap.add_argument("--archive", default="04-Archive")
    ap.add_argument("--me", default="05-Me")
    ap.add_argument("--data-root", default="数据")
    ap.add_argument("--force", action="store_true", help="已存在也覆盖")
    ap.add_argument("--dry-run", action="store_true", help="只打印，不写文件")
    args = ap.parse_args()

    if args.list:
        print("模块                        管哪层         默认")
        print("-" * 52)
        for name, (layer, default) in MODULES.items():
            print(f"{name:<28}{layer:<14}{'是' if default else '按需'}")
        print("\n默认四件套：" + "、".join(DEFAULTS))
        return 0

    if not args.target:
        raise SystemExit("缺少 --target；先用 --list 看有哪些模块")
    target = os.path.abspath(args.target)
    if not os.path.isdir(target):
        raise SystemExit(f"目标目录不存在：{target}")

    root = skill_root()
    values = {
        "{{INBOX}}": args.inbox,
        "{{PROJECTS}}": args.projects,
        "{{AREAS}}": args.areas,
        "{{KNOWLEDGE}}": args.knowledge,
        "{{ARCHIVE}}": args.archive,
        "{{ME}}": args.me,
        "{{DATA_ROOT}}": args.data_root,
        "{{DATE}}": datetime.date.today().isoformat(),
        "{{date}}": datetime.date.today().isoformat(),
        "{{ROOT}}": target,
        "{{SKILL_ROOT}}": root,
    }

    names = parse_modules(args.modules)
    out_base = os.path.join(target, ".claude", "skills")
    print(f"目标：{target}")
    print(f"模块：{', '.join(names)}")
    print(f"装到：{out_base}")
    print("-" * 60)

    written = skipped = 0
    for name in names:
        src_dir = os.path.join(root, "modules", name)
        src = os.path.join(src_dir, "SKILL.md")
        if not os.path.isfile(src):
            print(f"[缺] {name}: 找不到 {src}")
            continue
        for base, _, files in os.walk(src_dir):
            for fname in files:
                sfile = os.path.join(base, fname)
                rel = os.path.relpath(sfile, src_dir)
                dfile = os.path.join(out_base, name, rel)
                if os.path.exists(dfile) and not args.force:
                    print(f"[跳过] {name}/{rel}: 已存在（要覆盖加 --force）")
                    skipped += 1
                    continue
                if args.dry_run:
                    print(f"[预览] {name}/{rel} -> {dfile}")
                    continue
                os.makedirs(os.path.dirname(dfile), exist_ok=True)
                if os.path.splitext(fname)[1].lower() in TEXT_EXT:
                    with open(sfile, "r", encoding="utf-8") as f:
                        text = f.read()
                    for key, val in values.items():
                        text = text.replace(key, val)
                    if "{{" in text:
                        left = text.split("{{", 1)[1].split("}}", 1)[0]
                        print(f"[警告] {name}/{rel} 还有占位符：{{{{{left}}}}}")
                    with open(dfile, "w", encoding="utf-8") as f:
                        f.write(text)
                else:
                    shutil.copy2(sfile, dfile)
                print(f"[装好] {name}/{rel}")
                written += 1

    print("-" * 60)
    print(f"完成：写 {written} 个文件，跳过 {skipped} 个。")
    if not args.dry_run and written:
        print("下一步：在新库里跑一遍 入口 -> 卡片 -> 项目 -> 复盘，跑通才算装上。")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
