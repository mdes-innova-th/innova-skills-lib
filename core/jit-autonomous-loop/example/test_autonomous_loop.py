"""Tests for the minimal autonomous-loop example."""
import json
import os
import subprocess
import sys
from pathlib import Path

import autonomous_loop as loop


class _Clock:
    def __init__(self):
        self.t = 100.0
    def __call__(self):
        self.t += 0.5
        return self.t


def test_run_cycle_ok():
    rec = loop.run_cycle(1, lambda: {"ok": True, "x": 1}, _Clock())
    assert rec["ok"] is True
    assert rec["cycle"] == 1
    assert rec["duration_s"] >= 0


def test_run_cycle_failure():
    rec = loop.run_cycle(2, lambda: {"ok": False}, _Clock())
    assert rec["ok"] is False


def test_run_cycle_exception():
    rec = loop.run_cycle(3, lambda: (_ for _ in ()).throw(RuntimeError("boom")), _Clock())
    assert rec["ok"] is False
    assert "RuntimeError" in rec["result"]["detail"]


def test_append_log(tmp_path):
    p = tmp_path / "loop.jsonl"
    loop.append_log({"cycle": 1}, p)
    loop.append_log({"cycle": 2}, p)
    lines = p.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
    assert json.loads(lines[0])["cycle"] == 1


def test_append_log_bad_path_does_not_raise():
    loop.append_log({"x": 1}, Path("\x00/invalid/loop.jsonl"))


def test_singleton_acquired_once():
    loop.MUTEX = r"Local\test_example_singleton_1"
    assert loop.acquire_singleton() is True
    if loop._LOCK_HANDLE:
        ctypes = sys.modules["ctypes"]
        try:
            ctypes.windll.kernel32.CloseHandle(loop._LOCK_HANDLE)
        except Exception:
            pass
        loop._LOCK_HANDLE = None


def test_singleton_excludes_second_process(tmp_path):
    loop.MUTEX = r"Local\test_example_singleton_2"
    assert loop.acquire_singleton() is True
    script = f"""
import sys, os
sys.path.insert(0, r'{loop.ROOT}')
import autonomous_loop as loop
loop.MUTEX = r'{loop.MUTEX}'
print(loop.acquire_singleton())
"""
    proc = loop.pythonw_safe_run([sys.executable, "-c", script], timeout=30)
    assert proc.returncode == 0, proc.stderr
    assert proc.stdout.strip() == "False"
    if loop._LOCK_HANDLE:
        ctypes = sys.modules["ctypes"]
        try:
            ctypes.windll.kernel32.CloseHandle(loop._LOCK_HANDLE)
        except Exception:
            pass
        loop._LOCK_HANDLE = None


def test_pythonw_safe_run_does_not_inherit_stdin():
    env = {**os.environ, "LOOP_MUTEX": r"Local\test_example_singleton_3"}
    proc = loop.pythonw_safe_run([sys.executable, "-c", "print('ok')"], timeout=10, env=env)
    assert proc.returncode == 0
    assert "ok" in proc.stdout
