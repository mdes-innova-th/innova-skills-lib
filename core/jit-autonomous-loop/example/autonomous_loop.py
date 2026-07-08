#!/usr/bin/env python3
"""Minimal example of the Jit autonomous-loop pattern.

Run:  python example/autonomous_loop.py --max-cycles 3
"""
from __future__ import annotations

import ctypes
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent
LOG = ROOT / "loop.jsonl"
MUTEX = os.environ.get("LOOP_MUTEX", r"Local\jit_autonomous_loop_example")
INTERVAL = int(os.environ.get("LOOP_INTERVAL", "300"))
_LOCK_HANDLE: Any | None = None


def run_cycle(cycle_no: int,
              do_work: Callable[[], dict],
              clock: Callable[[], float]) -> dict:
    """Pure cycle logic. Never raises."""
    started = clock()
    try:
        result = do_work()
    except Exception as e:  # noqa: BLE001
        result = {"ok": False, "detail": f"{type(e).__name__}: {e}"}
    return {
        "cycle": cycle_no,
        "ts": round(clock(), 3),
        "duration_s": round(clock() - started, 3),
        "ok": bool(result.get("ok")),
        "result": result,
    }


def append_log(record: dict, path: Path = LOG) -> None:
    """Append JSONL. Never raises."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except (OSError, ValueError, TypeError):
        pass


def acquire_singleton() -> bool:
    """True only if this process is the one and only loop instance."""
    global _LOCK_HANDLE
    try:
        kernel32 = ctypes.windll.kernel32
        kernel32.CreateMutexW.argtypes = [ctypes.c_void_p, ctypes.c_bool, ctypes.c_wchar_p]
        kernel32.CreateMutexW.restype = ctypes.c_void_p
        handle = kernel32.CreateMutexW(None, False, MUTEX)
        if not handle or kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
            if handle:
                kernel32.CloseHandle(handle)
            return False
        _LOCK_HANDLE = handle
        return True
    except Exception:  # noqa: BLE001
        return True


def pythonw_safe_run(cmd: list[str], timeout: int = 60, env: dict | None = None) -> subprocess.CompletedProcess:
    """Run a subprocess that works under pythonw on Windows."""
    kwargs: dict[str, Any] = {
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "stdin": subprocess.DEVNULL,
        "text": True,
        "timeout": timeout,
        "encoding": "utf-8",
        "errors": "replace",
        "env": env,
    }
    if sys.platform == "win32":
        kwargs["creationflags"] = 0x08000000  # CREATE_NO_WINDOW
    return subprocess.run(cmd, **kwargs)


def main() -> None:
    max_cycles = int(os.environ.get("LOOP_MAX_CYCLES", "0"))
    if not acquire_singleton():
        print("already running", flush=True)
        return
    cycle = 0
    while True:
        cycle += 1
        record = run_cycle(cycle, lambda: {"ok": True, "msg": "noop"}, time.monotonic)
        append_log(record)
        print(record, flush=True)
        if max_cycles and cycle >= max_cycles:
            break
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
