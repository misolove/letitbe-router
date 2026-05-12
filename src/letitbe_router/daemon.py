"""Foreground/background lifecycle helpers for the local lr API server."""

from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class DaemonPaths:
    state_dir: Path
    pid_file: Path
    log_file: Path
    metadata_file: Path


def daemon_paths() -> DaemonPaths:
    state_dir = Path(
        os.environ.get("LETITBE_ROUTER_STATE_DIR", "~/.local/state/letitbe-router")
    ).expanduser()
    return DaemonPaths(
        state_dir=state_dir,
        pid_file=state_dir / "server.pid",
        log_file=state_dir / "server.log",
        metadata_file=state_dir / "server.json",
    )


def read_pid(paths: DaemonPaths | None = None) -> int | None:
    paths = paths or daemon_paths()
    try:
        raw_pid = paths.pid_file.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return None
    if not raw_pid:
        return None
    try:
        return int(raw_pid)
    except ValueError:
        return None


def is_process_running(pid: int | None) -> bool:
    if pid is None or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def _read_metadata(paths: DaemonPaths) -> dict[str, object] | None:
    try:
        payload = json.loads(paths.metadata_file.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return None
    return payload if isinstance(payload, dict) else None


def _write_metadata(
    paths: DaemonPaths, *, pid: int, command: list[str], host: str, port: int
) -> None:
    paths.metadata_file.write_text(
        json.dumps(
            {
                "pid": pid,
                "command": command,
                "host": host,
                "port": port,
                "started_at": time.time(),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


def _metadata_matches(paths: DaemonPaths, pid: int | None) -> bool:
    metadata = _read_metadata(paths)
    if not metadata or metadata.get("pid") != pid:
        return False
    command = metadata.get("command")
    if not isinstance(command, list):
        return False
    return "letitbe_router.cli" in command and "serve" in command


def _live_command_matches(pid: int) -> bool:
    try:
        result = subprocess.run(
            ["ps", "-p", str(pid), "-o", "command="],
            text=True,
            capture_output=True,
            timeout=2,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    if result.returncode != 0:
        return False
    command = result.stdout.strip()
    return "letitbe_router.cli" in command and " serve" in f" {command} "


def _owned_daemon_process(paths: DaemonPaths, pid: int | None) -> bool:
    if pid is None:
        return False
    return _metadata_matches(paths, pid) and _live_command_matches(pid)


def _cleanup_state(paths: DaemonPaths) -> None:
    for path in (paths.pid_file, paths.metadata_file):
        try:
            path.unlink()
        except FileNotFoundError:
            pass


def _wait_until_ready(
    host: str, port: int, process: subprocess.Popen, timeout_seconds: float = 5.0
) -> None:
    deadline = time.monotonic() + timeout_seconds
    url = f"http://{host}:{port}/health"
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"daemon exited during startup with code {process.returncode}")
        try:
            with urllib.request.urlopen(url, timeout=0.5) as response:
                if response.status == 200:
                    return
        except (OSError, urllib.error.URLError) as exc:
            last_error = exc
        time.sleep(0.1)
    raise RuntimeError(f"daemon did not become ready at {url}: {last_error}")


def render_daemon_status(*, base_url: str = "http://127.0.0.1:20128") -> str:
    paths = daemon_paths()
    pid = read_pid(paths)
    running = is_process_running(pid)
    status = "running" if running else "stopped"
    pid_text = str(pid) if pid is not None else "-"
    return "\n".join(
        [
            f"status: {status}",
            f"pid: {pid_text}",
            f"url: {base_url}",
            f"pid_file: {paths.pid_file}",
            f"log_file: {paths.log_file}",
        ]
    )


def start_daemon(
    *,
    host: str = "127.0.0.1",
    port: int = 20128,
    timeout_seconds: int = 120,
    dry_run: bool = False,
) -> tuple[int, Path]:
    paths = daemon_paths()
    existing_pid = read_pid(paths)
    if is_process_running(existing_pid):
        raise RuntimeError(f"daemon already running: pid {existing_pid}")
    paths.state_dir.mkdir(parents=True, exist_ok=True)
    command = [
        sys.executable,
        "-m",
        "letitbe_router.cli",
        "serve",
        "--host",
        host,
        "--port",
        str(port),
        "--timeout",
        str(timeout_seconds),
    ]
    if dry_run:
        command.append("--dry-run")
    log_handle = paths.log_file.open("ab")
    try:
        process = subprocess.Popen(
            command,
            stdin=subprocess.DEVNULL,
            stdout=log_handle,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    finally:
        log_handle.close()
    _write_metadata(paths, pid=process.pid, command=command, host=host, port=port)
    paths.pid_file.write_text(str(process.pid), encoding="utf-8")
    try:
        _wait_until_ready(host, port, process)
    except RuntimeError:
        process.terminate()
        try:
            process.wait(timeout=2)
        except subprocess.TimeoutExpired:
            process.kill()
        _cleanup_state(paths)
        raise
    return process.pid, paths.log_file


def stop_daemon() -> int | None:
    paths = daemon_paths()
    pid = read_pid(paths)
    if not is_process_running(pid):
        _cleanup_state(paths)
        return None
    if not _owned_daemon_process(paths, pid):
        _cleanup_state(paths)
        return None
    assert pid is not None
    os.kill(pid, signal.SIGTERM)
    _cleanup_state(paths)
    return pid
