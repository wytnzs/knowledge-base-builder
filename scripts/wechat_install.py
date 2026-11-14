#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""按需安装微信适配器。默认只打印方案，加 --yes 才执行网络/安装。

用法：
    python scripts/wechat_install.py --method wechat-cli-moments --dry-run
    python scripts/wechat_install.py --method wechat-cli-moments --yes

约定：
- 先征得本人同意，再执行 --yes；
- 只装到本机，不上传、不内置密钥；
- 密钥由 `wechat-cli init` 在本机提取，脚本不碰。
"""
import argparse
import os
import shutil
import subprocess
import sys

SKILL_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PATCH = os.path.join(SKILL_ROOT, "tools", "wechat", "patches", "wechat-cli-moments.patch")
UPSTREAM = "https://github.com/huohuoer/wechat-cli"
PINNED = "a3789232d4f79bf0b30634d9dadbce71e4acd601"
DEFAULT_DEST = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~/.local/share")),
    "kb-wechat", "wechat-cli")


def run(cmd, cwd=None):
    print("+ " + " ".join(cmd))
    p = subprocess.run(cmd, cwd=cwd)
    if p.returncode != 0:
        raise SystemExit(f"命令失败（{p.returncode}）：{' '.join(cmd)}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--method", required=True,
                    choices=["wechat-cli", "wechat-cli-moments", "wx", "chatlog-plus"])
    ap.add_argument("--dest", default=DEFAULT_DEST)
    ap.add_argument("--yes", action="store_true", help="真的执行安装")
    ap.add_argument("--dry-run", action="store_true", help="只打印，不执行")
    ap.add_argument("--force", action="store_true", help="目标目录已存在也继续")
    args = ap.parse_args()

    print("微信适配器安装")
    print("=" * 48)
    print("风险提示：读取微信本地数据库可能违反微信服务条款，存在账号风险；")
    print("聊天里有第三方隐私，只处理你有权访问的数据，只提炼，不搬运原文。")
    print("全程本机，不上传；密钥由本机 wechat-cli init 提取，不由本脚本处理。")
    print()

    if args.method == "wechat-cli":
        print("方案：公开 PyPI 包 wechat-cli（聊天；没有朋友圈）")
        print("命令：python -m pip install \"wechat-cli==0.2.6\"")
        if args.yes and not args.dry_run:
            run([sys.executable, "-m", "pip", "install", "wechat-cli==0.2.6"])
        return 0

    if args.method == "wechat-cli-moments":
        print("方案：wechat-cli + Moments 补丁（聊天 + 朋友圈）")
        print(f"上游：{UPSTREAM} @ {PINNED}")
        print(f"补丁：{PATCH}")
        print(f"目标：{args.dest}")
        if not os.path.isfile(PATCH):
            raise SystemExit(f"找不到补丁：{PATCH}")
        if os.path.exists(args.dest) and not args.force:
            print("目标目录已存在；要重装请加 --force，或换 --dest。")
            return 0
        commands = [
            ["git", "clone", UPSTREAM, args.dest, "--depth", "1"],
            ["git", "-C", args.dest, "fetch", "--depth", "1", "origin", PINNED],
            ["git", "-C", args.dest, "checkout", PINNED],
            ["git", "-C", args.dest, "apply", PATCH],
            [sys.executable, "-m", "pip", "install", "-e", args.dest],
        ]
        if args.yes and not args.dry_run:
            if not shutil.which("git"):
                raise SystemExit("找不到 git，请先安装 Git。")
            for cmd in commands:
                run(cmd)
            print()
            print("装好了。下一步（微信保持登录并停主窗口）：")
            print("  wechat-cli init")
            print("  wechat-cli moments feed --limit 5")
        else:
            print("将执行：")
            for cmd in commands:
                print("  " + " ".join(cmd))
            print("确认后加 --yes。")
        return 0

    if args.method == "wx":
        print("方案：wx-cli（三平台 + 朋友圈，但正式仓库私有、无公开 release）")
        print("本脚本不自动下载。若你已有 wx：")
        print("  wx sessions")
        print("  wx sns-feed --limit 20")
        print("若没有：需要源码构建（Rust/cargo）或向仓库维护者申请访问。")
        return 0

    if args.method == "chatlog-plus":
        print("方案：chatlog-plus（仅 Windows，本地自用）")
        print("本脚本不自动下载。已有安装时：")
        print("  python <chatlog-plus>/chatlog_plus.py moments person --name <姓名>")
        print("提示：上游 chatlog 已因微信官方函件删库；不要把它作为公开分发的默认工具。")
        return 0

    return 2


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass
    sys.exit(main())
