# -*- coding: utf-8 -*-
"""知识库基座的结构测试：模块登记、两种装法、体检 profile。"""
import json
import os
import subprocess
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PY = sys.executable


def run(script, *args):
    env = dict(os.environ, PYTHONUTF8="1", PYTHONIOENCODING="utf-8")
    proc = subprocess.run(
        [PY, os.path.join(ROOT, "scripts", script), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=ROOT, env=env,
    )
    return proc.returncode, (proc.stdout or "") + (proc.stderr or "")


def write(path, text):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)


def make_lib(tmp, roles=None, with_area=True):
    roles = roles or {
        "inbox": "00-Inbox", "projects": "01-Projects", "areas": "02-Areas",
        "knowledge": "03-Knowledge", "archive": "04-Archive", "me": "05-Me",
    }
    for name in roles.values():
        if name == "02-Areas" and not with_area:
            continue
        os.makedirs(os.path.join(tmp, name), exist_ok=True)
    base = {
        "base": "knowledge-base-builder", "version": "2.0.0", "contract": 2,
        "agent": {"primary": "claude-code", "rules": "AGENTS.md",
                  "adapters": ["CLAUDE.md"], "modules_mode": "skills",
                  "skills_dir": ".claude/skills"},
        "roles": roles, "modules": [], "loops": ["周三发公众号"], "data_root": "数据",
    }
    write(os.path.join(tmp, ".kb-base.json"), json.dumps(base, ensure_ascii=False))
    write(os.path.join(tmp, "README.md"), "---\ntitle: 库\ntype: index\n---\n# 库\n")
    write(os.path.join(tmp, "分区职责表.md"), "---\ntitle: 分区\ntype: zone_map\n---\n")
    write(os.path.join(tmp, "写入规则.md"), "---\ntitle: 写入\ntype: write_rules\n---\n")
    write(os.path.join(tmp, "AGENTS.md"), "---\ntitle: 规则\ntype: agent_rules\n---\n## 启动顺序\n")
    write(os.path.join(tmp, "工作回路.md"), "---\ntitle: 回路\ntype: work_loop\n---\n触发：周三\n读什么：05-Me\n产出什么：初稿\n写回什么：项目\n")
    write(os.path.join(tmp, "建库进度.md"), "---\ntitle: 进度\ntype: build_status\n---\n")
    write(os.path.join(tmp, "05-Me", "我是谁.md"), "---\ntitle: 我是谁\ntype: identity\n---\n")
    write(os.path.join(tmp, "采用计划.md"), "---\ntitle: 采用计划\ntype: plan_adoption\n---\n")
    write(os.path.join(tmp, "采用记录.md"),
          "---\ntitle: 采用\ntype: adoption_log\n---\n| 日期 | 回路 |\n|---|---|\n| 2026-11-14 | 周三发公众号 |\n")
    return base


class RegistryTest(unittest.TestCase):
    def test_contract_and_modules(self):
        with open(os.path.join(ROOT, "modules", "manifest.json"), encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data["contract"], 2)
        self.assertEqual(len(data["modules"]), 8)
        self.assertEqual(len([m for m in data["modules"] if m.get("default")]), 5)


class InstallTest(unittest.TestCase):
    def test_claude_code_skills(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_lib(tmp)
            code, out = run("install_modules.py", "--target", tmp,
                            "--agent", "claude-code", "--modules", "knowledge-card")
            self.assertEqual(code, 0, out)
            main = os.path.join(tmp, ".claude", "skills", "knowledge-card", "SKILL.md")
            self.assertTrue(os.path.isfile(main), out)
            with open(main, encoding="utf-8") as f:
                self.assertNotIn("{{", f.read())
            with open(os.path.join(tmp, ".kb-base.json"), encoding="utf-8") as f:
                base = json.load(f)
            self.assertEqual(base["agent"]["primary"], "claude-code")
            self.assertIn("knowledge-card", base["modules"])

    def test_workbuddy_checklists(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_lib(tmp)
            code, out = run("install_modules.py", "--target", tmp,
                            "--agent", "workbuddy", "--modules", "knowledge-card")
            self.assertEqual(code, 0, out)
            main = os.path.join(tmp, "操作模块", "knowledge-card.md")
            self.assertTrue(os.path.isfile(main), out)
            self.assertFalse(os.path.isdir(os.path.join(tmp, ".claude", "skills")))
            with open(os.path.join(tmp, ".kb-base.json"), encoding="utf-8") as f:
                base = json.load(f)
            self.assertEqual(base["agent"]["modules_mode"], "checklists")

    def test_missing_role_is_skipped(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_lib(tmp, with_area=False)
            code, out = run("install_modules.py", "--target", tmp,
                            "--modules", "area-review")
            self.assertEqual(code, 0, out)
            self.assertIn("跳过", out)
            self.assertFalse(os.path.exists(
                os.path.join(tmp, ".claude", "skills", "area-review", "SKILL.md")))


class WeChatTest(unittest.TestCase):
    def test_probe_json(self):
        code, out = run("wechat_probe.py")
        self.assertEqual(code, 0, out)
        data = json.loads(out)
        self.assertIn("adapters", data)
        self.assertIn("recommendation", data)

    def test_install_dry_run(self):
        code, out = run("wechat_install.py", "--method", "wechat-cli-moments", "--dry-run")
        self.assertEqual(code, 0, out)
        self.assertIn("git clone", out)
        self.assertIn("--yes", out)

    def test_discover_person(self):
        with tempfile.TemporaryDirectory() as tmp:
            write(os.path.join(tmp, ".claude", "skills", "demo", "SKILL.md"),
                  "---\nname: demo-skill\ndescription: 一个 demo\n---\n")
            write(os.path.join(tmp, "01-Projects", "p", "项目.md"),
                  "---\ntitle: 测试项目\ntype: project_status\nstatus: 进行中\nnext_action: 做一件事\n---\n")
            code, out = run("discover_person.py", "--root", tmp)
            self.assertEqual(code, 0, out)
            data = json.loads(out)
            self.assertEqual(data["skills"][0]["name"], "demo-skill")
            self.assertEqual(data["projects"][0]["title"], "测试项目")


class CheckTest(unittest.TestCase):
    def test_base_profile_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_lib(tmp)
            code, out = run("check_kb.py", "--root", tmp, "--profile", "base")
            self.assertEqual(code, 0, out)
            self.assertIn("都齐了", out)

    def test_v0_profile_passes(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_lib(tmp)
            code, out = run("check_kb.py", "--root", tmp, "--profile", "v0")
            self.assertEqual(code, 0, out)
            self.assertIn("都齐了", out)

    def test_use_profile_requires_adoption_row(self):
        with tempfile.TemporaryDirectory() as tmp:
            make_lib(tmp)
            write(os.path.join(tmp, "采用记录.md"),
                  "---\ntitle: 采用\ntype: adoption_log\n---\n| 日期 | 回路 |\n|---|---|\n|  |  |\n")
            code, out = run("check_kb.py", "--root", tmp, "--profile", "use")
            self.assertEqual(code, 0, out)
            self.assertIn("MISS", out)
            self.assertIn("采用记录", out)


if __name__ == "__main__":
    unittest.main()
