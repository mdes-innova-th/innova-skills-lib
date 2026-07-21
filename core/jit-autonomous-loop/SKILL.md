---
name: jit-autonomous-loop
description: |
  Build durable, output-validated 24/7 autonomous loops on Windows: singleton enforcement,
  pythonw-safe subprocess, cycle-based workload, JSONL health log, provider health probes,
  and operational hygiene watchers (handoff inbox, progress tick). Proven in Jit + URL-Checker.
---

# Jit Autonomous Loop

A reusable pattern for running a self-checking, self-reporting autonomous loop on Windows
that survives pythonw, stray launches, console encoding issues, and flaky providers.

## When to use this

- You need a 24/7 background loop every 5–15 minutes.
- The loop must never silently run twice (e.g. a `pythonw` shim + base interpreter pair).
- The loop delegates work to external providers/children and must not trust exit code alone.
- You want JSONL logs, health snapshots, and alerts a human can read without logging into the box.

## Core principles

1. **Output wins over exit code.** A child can exit 0 with empty stdout. Always validate the returned text.
2. **Singleton via Windows named mutex.** PID files and file locks are not enough when `pythonw.exe` + `python.exe` both exist.
3. **pythonw-safe subprocess.** Use `stdout/stderr=PIPE`, `stdin=DEVNULL`, `creationflags=CREATE_NO_WINDOW` to avoid `OSError: [WinError 50]`.
4. **Never let logging crash the loop.** Every log write is wrapped so a bad path or record is archived, not fatal.
5. **Branch the workload by cycle.** Fast cheap check every tick; expensive full check every N ticks.
6. **Atomic writes for state files.** Write to `.tmp`, then `os.replace`.
7. **Force UTF-8 stdout/stderr on Windows.** The default cp1252 console crashes on `ψ/`, Thai, or emoji; reconfigure to `utf-8` at entry.

## Pattern A: Windows named-mutex singleton loop

### File: `autonomous_loop.py`

```python
"""Minimal durable autonomous loop."""
from __future__ import annotations

import atexit
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
MUTEX = os.environ.get("LOOP_MUTEX", r"Local\my_loop_singleton")
INTERVAL = int(os.environ.get("LOOP_INTERVAL", "300"))
MAX_LOG_BYTES = int(os.environ.get("LOOP_MAX_LOG_BYTES", str(50 * 1024 * 1024)))
_LOCK_HANDLE: Any | None = None


def _release_singleton() -> None:
    """Best-effort release of the Windows named mutex handle on exit."""
    global _LOCK_HANDLE
    if _LOCK_HANDLE and sys.platform == "win32":
        try:
            ctypes.windll.kernel32.CloseHandle(_LOCK_HANDLE)
        except Exception:  # noqa: BLE001
            pass
        _LOCK_HANDLE = None


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
    """Append JSONL. Never raises. Rotates when the log grows too large."""
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.exists() and path.stat().st_size >= MAX_LOG_BYTES:
            rotated = path.with_name(f"{path.stem}_{time.strftime('%Y%m%d_%H%M%S')}{path.suffix}")
            os.rename(path, rotated)
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
        atexit.register(_release_singleton)
        return True
    except Exception:  # noqa: BLE001 — non-Windows fallback
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
    if not acquire_singleton():
        print("already running", flush=True)
        return
    cycle = 0
    while True:
        cycle += 1
        record = run_cycle(cycle, lambda: {"ok": True, "msg": "noop"}, time.monotonic)
        append_log(record)
        print(record, flush=True)
        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()
```

### Singleton test

```python
# test_singleton.py
import sys
import pytest

@pytest.mark.skipif(sys.platform != "win32", reason="Windows named mutex only")
def test_second_process_fails_to_acquire_mutex(tmp_path):
    import autonomous_loop as loop
    loop.MUTEX = r"Local\test_my_loop_singleton"
    assert loop.acquire_singleton() is True
    script = f"""
import sys, os
sys.path.insert(0, r'{loop.ROOT}')
import autonomous_loop as loop
loop.MUTEX = r'{loop.MUTEX}'
print(loop.acquire_singleton())
"""
    proc = loop.pythonw_safe_run([sys.executable, "-c", script], timeout=30)
    assert proc.stdout.strip() == "False"
```

## Pattern B: Output-validated provider health probe

```python
def non_empty(text: str) -> bool:
    return bool(text and text.strip())


def smoke_provider(call_provider: Callable[[str], str], probe: str = "Reply exactly: OK") -> dict:
    t0 = time.time()
    out = call_provider(probe)
    return {
        "proven": non_empty(out),
        "latency_s": round(time.time() - t0, 2),
        "sample": (out or "").replace("\n", " ")[:80],
    }
```

- `call_provider` can be HTTP, CLI, or file bus. The caller decides.
- A probe is **proven** only when it returns non-empty text matching the expected shape.
- Store a health snapshot to disk so the orchestrator can skip dead providers without re-probing.

## Pattern C: Operational hygiene watchers

### Progress tick

```python
def tick(state_file: Path, max_history: int = 100) -> dict:
    state = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {"ticks": 0}
    state["ticks"] = state.get("ticks", 0) + 1
    state["last_tick"] = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    state.setdefault("history", []).append({"ts": state["last_tick"]})
    state["history"] = state["history"][-max_history:]
    tmp = state_file.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, state_file)
    return state
```

Run via Windows Task Scheduler every 5 minutes. A caretaker can call `python tick.py --status` and exit 1 if `delta_min > 10`.

### Handoff inbox watcher

```python
def unread_handoffs(inbox: Path, now: float | None = None) -> list[Path]:
    now = now or time.time()
    unread = []
    for p in inbox.glob("*.md"):
        if p.name.startswith("auto-compact-") or p.name in ("INDEX.md",):
            continue
        age_min = (now - p.stat().st_mtime) / 60
        if p.stat().st_size > 100 and 10 < age_min < 60 * 24:
            unread.append(p)
    return unread
```

> Caveat: mtime is modification time, not read time. Move acknowledged handoffs to an `archive/` folder so they stop being counted.

## Checklist before shipping a loop

- [ ] Singleton works across `python.exe` and `pythonw.exe`.
- [ ] Subprocess runners use `PIPE`, `DEVNULL`, `CREATE_NO_WINDOW`.
- [ ] Cycle logic is pure/injectable for tests.
- [ ] Log writes never raise.
- [ ] Provider probes validate output, not exit code.
- [ ] Health snapshot is written to disk.
- [ ] Fast check every tick; full check every N ticks.
- [ ] A stalled/dead loop is detectable by a separate watcher.
- [ ] Entry point reconfigures stdout/stderr to UTF-8 so paths/emoji don't crash on cp1252.

## Testing strategy

1. **Pure cycle tests** — inject deterministic `do_work` and `clock`, assert JSON output.
2. **Singleton tests** — spawn a second Python process and assert it cannot acquire the mutex.
3. **Subprocess tests** — verify the `pythonw_safe_run` kwargs avoid `WinError 50` under `pythonw`.
4. **Provider tests** — mock provider call to return empty/valid/exception, assert `proven`.
5. **Log durability tests** — write to invalid path, assert no exception.
6. **End-to-end** — run the loop for 3 cycles with `MAX_CYCLES=3`, inspect JSONL.

## Pitfalls

- **Trusting exit code.** Always pair `returncode == 0` with output validation.
- **PID-file singleton.** A stale PID file or two interpreter variants will let duplicates run.
- **Console-only subprocess.** `stdin=None` (inherited) can break under `pythonw`.
- **Unbounded logs / history.** Cap arrays and rotate JSONL.
- **No stall detection.** A loop that hangs silently looks healthy; add an external tick watcher.
- **cp1252 console crash.** Any watcher/CLI that prints `ψ`, Thai, or emoji must call `sys.stdout.reconfigure(encoding="utf-8")` at entry.

## Example command reference

```bash
# Run one tick manually
python example/autonomous_loop.py

# Check singleton behavior
python example/test_singleton.py

# Run provider health probe (adapter required)
python my_health_probe.py

# Verify progress tick is alive
python tools/jit_progress_tick.py --status || echo "STALLED"

# Check for unread handoffs
python tools/handoff_inbox_watcher.py || echo "HANDOFFS PENDING"
```

## References

- Proven in `Jit/tools/jit_progress_tick.py`
- Proven in `Jit/tools/handoff_inbox_watcher.py`
- Proven in `DEV/URL-Checker/csoc_boi/auto_verify_loop.py`
- Proven in `Jit/tools/provider_fleet.py`

> **Natural /workflow-codify trigger**: If you find yourself adapting this loop pattern for a third project or a third distinct workload, run `/workflow-codify` to extract the project-specific parts into a dedicated skill so future loops can bootstrap from a spec instead of copying this file.
