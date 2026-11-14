#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
把日常模块装进一个知识库，并把基座状态写进 .kb-base.json。

跨 Agent：
    --agent claude-code   → .claude/skills/<模块>/SKILL.md
    --agent codex         → skills/<模块>/SKILL.md
    --agent workbuddy     → 操作模块/<模块>.md（清单模式）
    --agent generic       → 操作模块/<模块>.md（清单模式）

用法：
    python install_modules.py --list
    python install_modules.py --target "D:/我的知识库"
    python install_modules.py --target "D:/我的知识库" --agent workbuddy
    python install_modules.py --target "D:/我的知识库" --modules inbox-triage,knowledge-card

装法：按 modules/manifest.json 认模块，把 modules/<名字>/ 整个目录复制到目标位置，
文本文件里的占位符换成本库实际路径。已存在的不覆盖，除非 --force。

角色目录优先从目标库的 .kb-base.json 读；没有才用命令行参数和默认名。
装完更新 .kb-base.json：角色映射、Agent 适配、基座版本、已装模块。
"""
import argparse
import datetime
import json
import os
import shutil
import sys

BASE_VERSION = "2.1.0"
SUPPORTED_CONTRACT = 2
BASE_FILE = ".kb-base.json"
MODULE_SRC = "SKILL.template.md"
ROLE_KEYS = ["inbox", "projects", "areas", "knowledge", "archive", "me"]
DEFAULT_ROLES = {
    "inbox": "00-Inbox",
    "projects": "01-Projects",
    "areas": "02-Areas",
    "knowledge": "03-Knowledge",
    "archive": "04-Archive",
    "me": "05-Me",
}
AGENTS = {
    "claude-code": {
        "rules": "AGENTS.md",
        "adapters": ["CLAUDE.md"],
        "modules_mode": "skills",
        "skills_dir": ".claude/skills",
    },
    "codex": {
        "rules": "AGENTS.md",
        "adapters": [],
        "modules_mode": "skills",
        "skills_dir": "skills",
    },
    "workbuddy": {
        "rules": "AGENTS.md",
        "adapters": ["AI协作规则.md"],
        "modules_mode": "checklists",
        "skills_dir": None,
    },
    "generic": {
        "rules": "AGENTS.md",
        "adapters": ["AI协作规则.md"],
        "modules_mode": "checklists",
        "skills_dir": None,
    },
}
TEXT_EXT = {".md", ".json", ".py", ".txt", ".yaml", ".yml", ".csv", ".html", ".css", ".js"}


def skill_root():
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def load_registry(root):
    path = os.path.join(root, "modules", "manifest.json")
    if not os.path.isfile(path):
        raise SystemExit(f"找不到模块登记表：{path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    contract = data.get("contract")
    if contract != SUPPORTED_CONTRACT:
        raise SystemExit(
            f"模块契约版本不匹配：登记表是 {contract}，本脚本支持 {SUPPORTED_CONTRACT}。"
            "先升级 skill，别硬装。"
        )
    return data.get("modules", [])


def load_base(target):
    path = os.path.join(target, BASE_FILE)
    if not os.path.isfile(path):
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, ValueError) as exc:
        raise SystemExit(f"{BASE_FILE} 读不了：{exc}。先修好它，别覆盖。")


def resolve_roles(target, base, args):
    """返回（替换用角色表, 已声明角色表）。"""
    if base:
        declared = {k: v for k, v in (base.get("roles") or {}).items()
                    if k in ROLE_KEYS and v}
    else:
        declared = {}
    for key in ROLE_KEYS:
        value = getattr(args, key, None)
        if value:
            declared[key] = value
    if not base:
        for key in ROLE_KEYS:
            if key not in declared and os.path.isdir(os.path.join(target, DEFAULT_ROLES[key])):
                declared[key] = DEFAULT_ROLES[key]
    roles = dict(DEFAULT_ROLES)
    roles.update(declared)
    return roles, declared


def resolve_agent(base, args):
    """命令行 > .kb-base.json > 默认 claude-code。"""
    known = (base or {}).get("agent") or {}
    primary = args.agent or known.get("primary") or "claude-code"
    if primary not in AGENTS:
        raise SystemExit(f"不认识的 Agent：{primary}；可选：{', '.join(AGENTS)}")
    config = dict(AGENTS[primary])
    if args.modules_mode:
        config["modules_mode"] = args.modules_mode
    if args.skills_dir:
        config["skills_dir"] = args.skills_dir
    if config["modules_mode"] == "skills" and not config["skills_dir"]:
        config["skills_dir"] = ".claude/skills" if primary == "claude-code" else "skills"
    if config["modules_mode"] == "checklists":
        config["skills_dir"] = None
    config["primary"] = primary
    return config


def missing_roles(target, roles, declared, required):
    return [key for key in required
            if key not in declared or not os.path.isdir(os.path.join(target, roles[key]))]


def output_paths(target, agent, name):
    if agent["modules_mode"] == "skills":
        base = os.path.join(target, agent["skills_dir"], name)
        return os.path.join(base, "SKILL.md"), base
    base = os.path.join(target, "操作模块")
    return os.path.join(base, f"{name}.md"), os.path.join(base, name)


def stamp_base(target, base, declared, installed, data_root, agent, dry_run):
    if dry_run:
        print(f"[预览] 更新 {BASE_FILE}：角色 + Agent + 已装模块")
        return
    today = datetime.date.today().isoformat()
    data = dict(base) if base else {}
    data["base"] = "knowledge-base-builder"
    data["version"] = BASE_VERSION
    data["contract"] = SUPPORTED_CONTRACT
    data.setdefault("created", today)
    data["updated"] = today
    data["agent"] = {
        "primary": agent["primary"],
        "rules": agent["rules"],
        "adapters": agent["adapters"],
        "modules_mode": agent["modules_mode"],
        "skills_dir": agent["skills_dir"],
    }
    data["roles"] = dict(declared)
    data["data_root"] = data_root
    data.setdefault("loops", [])
    old = []
    for m in data.get("modules") or []:
        old.append(m.get("name") if isinstance(m, dict) else m)
    names = sorted({n for n in old + installed if n})
    data["modules"] = names
    with open(os.path.join(target, BASE_FILE), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")
    print(f"[基座] 已更新 {BASE_FILE}：{len(names)} 个模块 / {agent['primary']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="列出模块")
    ap.add_argument("--target", help="知识库的根目录")
    ap.add_argument("--modules", default="default", help="default 或逗号分隔的模块名")
    ap.add_argument("--agent", choices=list(AGENTS), help="目标 Agent；不填读 .kb-base.json，再默认 claude-code")
    ap.add_argument("--modules-mode", choices=["skills", "checklists"], help="强制装成 skill 或清单")
    ap.add_argument("--skills-dir", help="skills 模式的安装目录，相对库根")
    for key in ROLE_KEYS:
        ap.add_argument(f"--{key}", help=f"{key} 角色对应的目录名")
    ap.add_argument("--data-root", help="外部数据仓目录名")
    ap.add_argument("--force", action="store_true", help="已存在也覆盖")
    ap.add_argument("--dry-run", action="store_true", help="只打印，不写文件")
    args = ap.parse_args()

    root = skill_root()
    registry = load_registry(root)
    by_name = {m["name"]: m for m in registry}
    defaults = [m["name"] for m in registry if m.get("default")]

    if args.list:
        print("模块                        版本    角色        默认  依赖")
        print("-" * 72)
        for m in registry:
            role = m.get("role") or "跨层"
            print(f"{m['name']:<28}{m.get('version', '-'):<8}{role:<12}"
                  f"{'是' if m.get('default') else '按需'}  "
                  f"{', '.join(m.get('requires') or []) or '-'}")
        print("\n默认五件套：" + "、".join(defaults))
        print("Agent：" + " / ".join(AGENTS))
        return 0

    if not args.target:
        raise SystemExit("缺少 --target；先用 --list 看有哪些模块")
    target = os.path.abspath(args.target)
    if not os.path.isdir(target):
        raise SystemExit(f"目标目录不存在：{target}")

    base = load_base(target)
    roles, declared = resolve_roles(target, base, args)
    agent = resolve_agent(base, args)
    data_root = args.data_root or (base or {}).get("data_root") or "数据"

    if args.modules == "default":
        names = defaults
    else:
        names = [x.strip() for x in args.modules.split(",") if x.strip()]
        unknown = [x for x in names if x not in by_name]
        if unknown:
            raise SystemExit(f"不认识的模块：{', '.join(unknown)}")

    values = {
        "{{INBOX}}": roles["inbox"],
        "{{PROJECTS}}": roles["projects"],
        "{{AREAS}}": roles["areas"],
        "{{KNOWLEDGE}}": roles["knowledge"],
        "{{ARCHIVE}}": roles["archive"],
        "{{ME}}": roles["me"],
        "{{DATA_ROOT}}": data_root,
        "{{DATE}}": datetime.date.today().isoformat(),
        "{{date}}": datetime.date.today().isoformat(),
        "{{ROOT}}": target,
        "{{SKILL_ROOT}}": root,
    }

    print(f"目标：{target}")
    print(f"Agent：{agent['primary']}（{agent['modules_mode']}）")
    print(f"角色：{', '.join(f'{k}={v}' for k, v in declared.items()) or '（未声明）'}")
    print(f"模块：{', '.join(names)}")
    print("-" * 64)

    written = skipped = blocked = 0
    installed = []
    for name in names:
        entry = by_name[name]
        miss = missing_roles(target, roles, declared, entry.get("requires") or [])
        if miss:
            print(f"[跳过] {name}: 缺角色 {', '.join(miss)}（目录不存在）")
            blocked += 1
            continue
        src_dir = os.path.join(root, "modules", name)
        src = os.path.join(src_dir, MODULE_SRC)
        if not os.path.isfile(src):
            print(f"[缺] {name}: 找不到 {src}")
            blocked += 1
            continue
        main_out, aux_out = output_paths(target, agent, name)
        module_written = 0
        for base_dir, _, files in os.walk(src_dir):
            for fname in files:
                sfile = os.path.join(base_dir, fname)
                rel = os.path.relpath(sfile, src_dir)
                dfile = main_out if rel == MODULE_SRC else os.path.join(aux_out, rel)
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
                print(f"[装好] {name}/{rel} -> {os.path.relpath(dfile, target)}")
                written += 1
                module_written += 1
        if module_written or os.path.exists(main_out):
            installed.append(name)

    print("-" * 64)
    print(f"完成：写 {written} 个文件，跳过 {skipped} 个，未装 {blocked} 个。")
    if not args.dry_run:
        stamp_base(target, base, declared, installed, data_root, agent, args.dry_run)
    if not os.path.isfile(os.path.join(target, agent["rules"])):
        print(f"提示：根目录还没有 {agent['rules']}（Agent 规则正文）。用 templates/AGENTS.md 生成一份。")
    if not args.dry_run and written:
        print("下一步：在新库里跑一遍第一条工作回路，跑通才算装上。")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
