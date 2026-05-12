import json
import subprocess

from letitbe_router.daemon import daemon_paths, render_daemon_status, stop_daemon


def test_daemon_paths_use_configurable_state_dir(tmp_path, monkeypatch):
    monkeypatch.setenv("LETITBE_ROUTER_STATE_DIR", str(tmp_path))

    paths = daemon_paths()

    assert paths.state_dir == tmp_path
    assert paths.pid_file == tmp_path / "server.pid"
    assert paths.log_file == tmp_path / "server.log"
    assert paths.metadata_file == tmp_path / "server.json"


def test_stop_daemon_does_not_kill_stale_pid_without_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("LETITBE_ROUTER_STATE_DIR", str(tmp_path))
    paths = daemon_paths()
    paths.state_dir.mkdir(parents=True, exist_ok=True)
    paths.pid_file.write_text("99999", encoding="utf-8")

    def fake_kill(pid, signal):
        if signal == 0:
            return None
        raise AssertionError("stop_daemon should not SIGTERM unverified PID")

    monkeypatch.setattr("letitbe_router.daemon.os.kill", fake_kill)

    stopped = stop_daemon()

    assert stopped is None
    assert not paths.pid_file.exists()


def test_stop_daemon_does_not_kill_stale_pid_with_stale_metadata(tmp_path, monkeypatch):
    monkeypatch.setenv("LETITBE_ROUTER_STATE_DIR", str(tmp_path))
    paths = daemon_paths()
    paths.state_dir.mkdir(parents=True, exist_ok=True)
    process = subprocess.Popen(["sleep", "30"])
    try:
        paths.pid_file.write_text(str(process.pid), encoding="utf-8")
        paths.metadata_file.write_text(
            json.dumps(
                {
                    "pid": process.pid,
                    "command": ["python", "-m", "letitbe_router.cli", "serve"],
                    "host": "127.0.0.1",
                    "port": 20128,
                }
            ),
            encoding="utf-8",
        )

        stopped = stop_daemon()

        assert stopped is None
        assert process.poll() is None
        assert not paths.pid_file.exists()
        assert not paths.metadata_file.exists()
    finally:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=5)


def test_render_daemon_status_reports_stopped_without_pid(tmp_path, monkeypatch):
    monkeypatch.setenv("LETITBE_ROUTER_STATE_DIR", str(tmp_path))

    text = render_daemon_status(base_url="http://127.0.0.1:20128")

    assert "status: stopped" in text
    assert "url: http://127.0.0.1:20128" in text
