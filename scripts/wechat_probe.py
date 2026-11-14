#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""探测本机微信读取能力（只读元数据，不读聊天/朋友圈正文）。

用法：
    python scripts/wechat_probe.py
    python scripts/wechat_probe.py --format text
    python scripts/wechat_probe.py --show-paths

输出给「了解你」这一步用：本机有没有微信、装了哪个适配器、
能不能读聊天、能不能读朋友圈、有没有 sns.db 的密钥。
"""
import argparse
import glob
import importlib.util
import json
import os
import platform
import shutil
import subprocess
import sys
import urllib.request

STATE_DIR = os.path.expanduser("~/.wechat-cli")
KEYS_FILE = os.path.join(STATE_DIR, "all_keys.json")
CONFIG_FILE = os.path.join(STATE_DIR, "config.json")
PLATFORM_NOTES = {
    "windows": "已验证；读 Weixin.exe 进程内存",
    "darwin": "Apple Silicon 大概率；Intel 缺 x86_64 取钥二进制；需 sudo / 完全磁盘访问",
    "linux": "未验证；需 root；依赖微信 Linux 客户端",
}


def _run(cmd, timeout=8):
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                           encoding="utf-8", errors="replace")
        return p.returncode, (p.stdout or "").strip(), (p.stderr or "").strip()
    except Exception as exc:
        return -1, "", str(exc)


def _wechat_data_dirs():
    system = platform.system().lower()
    roots = []
    if system == "windows":
        cfg_dir = os.path.join(os.environ.get("APPDATA", ""), "Tencent", "xwechat", "config")
        if os.path.isdir(cfg_dir):
            for ini in glob.glob(os.path.join(cfg_dir, "*.ini")):
                try:
                    text = None
                    for enc in ("utf-8", "gbk"):
                        try:
                            with open(ini, "r", encoding=enc) as f:
                                text = f.read(1024).strip()
                            break
                        except UnicodeDecodeError:
                            continue
                    if text and os.path.isdir(text):
                        roots.append(text)
                except OSError:
                    pass
        # 常见安装位置兜底：只查已知根目录，不扫全盘
        for candidate in (
            os.environ.get("WECHAT_DATA_ROOT", ""),
            r"D:\Weixin",
            r"D:\WeChat",
            r"C:\Weixin",
            r"C:\WeChat",
            os.path.expanduser("~/xwechat_files"),
            os.path.expanduser("~/Documents/xwechat_files"),
        ):
            if candidate and os.path.isdir(candidate):
                roots.append(candidate)
    elif system == "darwin":
        roots.append(os.path.expanduser(
            "~/Library/Containers/com.tencent.xinWeChat/Data/Documents/xwechat_files"))
    else:
        roots.append(os.path.expanduser("~/Documents/xwechat_files"))
        roots.append(os.path.expanduser("~/.local/share/weixin/data"))
    found = []
    seen = set()
    for root in roots:
        patterns = [
            os.path.join(root, "*", "db_storage"),
            os.path.join(root, "xwechat_files", "*", "db_storage"),
        ]
        for pattern in patterns:
            for match in glob.glob(pattern):
                normalized = os.path.normcase(os.path.normpath(match))
                if os.path.isdir(match) and normalized not in seen:
                    seen.add(normalized)
                    found.append(match)
    return sorted(found)


def _keys_info():
    info = {"present": os.path.isfile(KEYS_FILE), "count": 0, "sns_key": False}
    if not info["present"]:
        return info
    try:
        with open(KEYS_FILE, encoding="utf-8") as f:
            data = json.load(f)
        keys = {k: v for k, v in data.items() if not k.startswith("_")}
        info["count"] = len(keys)
        info["sns_key"] = any("sns" in k.lower() and "sns.db" in k.lower() for k in keys)
    except (OSError, ValueError):
        info["error"] = True
    return info


def _wechat_cli_info():
    exe = shutil.which("wechat-cli")
    module_ok = importlib.util.find_spec("wechat_cli") is not None
    info = {
        "installed": bool(exe or module_ok),
        "executable": exe or "",
        "module": module_ok,
        "version": "",
        "chat": False,
        "moments": False,
    }
    if not (exe or module_ok):
        return info
    if exe:
        code, out, _ = _run([exe, "--version"])
        if code == 0:
            info["version"] = out
        code, _, _ = _run([exe, "moments", "--help"])
        info["moments"] = code == 0
        code, _, _ = _run([exe, "sessions", "--help"])
        info["chat"] = code == 0
    elif module_ok:
        try:
            from wechat_cli.commands import moments as _moments  # noqa: F401
            info["moments"] = True
        except Exception:
            info["moments"] = False
        info["chat"] = True
    return info


def _wx_info():
    exe = shutil.which("wx")
    info = {"installed": bool(exe), "executable": exe or "", "chat": False, "moments": False}
    if not exe:
        return info
    code, _, _ = _run([exe, "sessions", "--help"])
    info["chat"] = code == 0
    code, _, _ = _run([exe, "sns-feed", "--help"])
    info["moments"] = code == 0
    return info


def _chatlog_plus_info():
    info = {"installed": False, "running": False, "moments": False}
    try:
        with urllib.request.urlopen("http://127.0.0.1:5031/health", timeout=1.5) as r:
            info["running"] = r.status == 200
    except Exception:
        info["running"] = False
    info["installed"] = info["running"] or os.path.isdir(
        os.path.expanduser("~/AppData/Local/WeChatChatlogStack"))
    info["moments"] = info["running"]
    return info


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--format", choices=["json", "text"], default="json")
    ap.add_argument("--show-paths", action="store_true", help="输出账号目录路径")
    args = ap.parse_args()

    dirs = _wechat_data_dirs()
    keys = _keys_info()
    cli = _wechat_cli_info()
    wx = _wx_info()
    plus = _chatlog_plus_info()

    chat = "wechat-cli" if cli["chat"] else ("wx" if wx["chat"] else (
        "chatlog-plus" if plus["running"] else "none"))
    moments = "wechat-cli" if cli["moments"] else ("wx" if wx["moments"] else (
        "chatlog-plus" if plus["moments"] else "none"))

    system = platform.system().lower()
    payload = {
        "os": system,
        "platform_notes": PLATFORM_NOTES.get(system, "未验证"),
        "wechat": {
            "db_storage_count": len(dirs),
            "db_storage": dirs if args.show_paths else [],
            "keys": keys,
            "config": os.path.isfile(CONFIG_FILE),
        },
        "adapters": {
            "wechat-cli": cli,
            "wx": wx,
            "chatlog-plus": plus,
        },
        "recommendation": {"chat": chat, "moments": moments},
    }

    if args.format == "json":
        json.dump(payload, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    print(f"系统：{payload['os']}（{payload['platform_notes']}）")
    print(f"微信数据目录：{len(dirs)} 个" + ("" if not args.show_paths else "：" + "、".join(dirs)))
    print(f"密钥文件：{'有' if keys['present'] else '没有'}，{keys['count']} 个库"
          + ("，含 sns.db" if keys["sns_key"] else "，不含 sns.db"))
    print(f"wechat-cli：{'装了' if cli['installed'] else '没装'}"
          + (f"，聊天{'可' if cli['chat'] else '不可'}，朋友圈{'可' if cli['moments'] else '不可'}"
             if cli["installed"] else ""))
    print(f"wx：{'装了' if wx['installed'] else '没装'}"
          + (f"，聊天{'可' if wx['chat'] else '不可'}，朋友圈{'可' if wx['moments'] else '不可'}"
             if wx["installed"] else ""))
    print(f"chatlog-plus：{'运行中' if plus['running'] else '未运行'}")
    print(f"建议：聊天用 {chat}，朋友圈用 {moments}")
    return 0


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
