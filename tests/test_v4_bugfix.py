#!/usr/bin/env python3
"""Regression tests for laoshifu V4.0.1 portability and validator fixes."""
from __future__ import annotations
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"


def node_command():
    configured = os.environ.get("NODE") or os.environ.get("NODEJS")
    candidates = [configured, shutil.which(configured) if configured else None,
                  shutil.which("node"), shutil.which("nodejs"),
                  "/usr/local/lib/python3.11/site-packages/playwright/driver/node",
                  "/usr/local/lib/python3.11/site-packages/patchright/driver/node",
                  "/usr/local/bin/node", "/usr/bin/node"]
    for candidate in candidates:
        if candidate and Path(candidate).is_file() and os.access(candidate, os.X_OK):
            return candidate
    raise RuntimeError("Node.js runtime not found")


NODE = node_command()


def run(*args, cwd=None):
    proc = subprocess.run(args, cwd=cwd, capture_output=True, text=True, encoding="utf-8")
    if proc.returncode:
        raise AssertionError(f"command failed ({proc.returncode}): {' '.join(map(str, args))}\n{proc.stdout}\n{proc.stderr}")
    return proc


def test_portable_fusion_from_foreign_cwd():
    question = '这个月底前甲方会签合同吗？ | "; & echo should-not-run'
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "fusion.json"
        run(sys.executable, SCRIPTS / "liuyao_qimen_fusion.py", f"--question={question}",
            "--category=career", "--method=numbers", "--numbers=12,35,8",
            "--year=2026", "--month=8", "--day=29", "--hour=15", "--minute=0",
            "--timeZone=8", f"--output={output}", cwd=Path.cwd())
        data = json.loads(output.read_text(encoding="utf-8"))
        assert data["schemaVersion"] == "aceworld-liuyao-qimen-fusion.v2"
        assert data["question"]["text"] == question
        assert data["methods"]["liuyao"]["本卦"]
        assert data["methods"]["qimen"]["局数"]


def test_lichun_year_boundary_after():
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "after.json"
        run(NODE, SCRIPTS / "resolve-pillars.cjs", "--pillars=甲辰 丙寅 戊戌 甲子",
            "--startYear=2024", "--endYear=2024", f"--output={output}")
        data = json.loads(output.read_text(encoding="utf-8"))
        assert any(c["date"] == "2024-02-04" for c in data["candidates"])


def test_lichun_year_boundary_before():
    with tempfile.TemporaryDirectory() as tmp:
        output = Path(tmp) / "before.json"
        run(NODE, SCRIPTS / "resolve-pillars.cjs", "--pillars=癸卯 乙丑 戊戌 壬子",
            "--startYear=2024", "--endYear=2024", f"--output={output}")
        data = json.loads(output.read_text(encoding="utf-8"))
        assert any(c["date"] == "2024-02-04" for c in data["candidates"])


def test_no_author_machine_path_in_active_route():
    for name in ("liuyao_qimen_fusion.py", "heixiang_fusion.py", "chart_bazi_ziwei.py"):
        text = (SCRIPTS / name).read_text(encoding="utf-8")
        assert "/root/.openclaw" not in text


if __name__ == "__main__":
    for test in (test_portable_fusion_from_foreign_cwd, test_lichun_year_boundary_after,
                 test_lichun_year_boundary_before, test_no_author_machine_path_in_active_route):
        test()
        print(f"PASS {test.__name__}")