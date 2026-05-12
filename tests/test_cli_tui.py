import subprocess
import sys


def test_cli_tui_once_renders_9router_style_menu():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "letitbe_router.cli",
            "tui",
            "--once",
            "--base-url",
            "http://localhost:20128",
        ],
        text=True,
        capture_output=True,
        check=True,
    )

    assert "Choose Interface" in result.stdout
    assert "Server: http://localhost:20128" in result.stdout
    assert "OpenAI API" in result.stdout
    assert "Terminal UI" in result.stdout
    assert "Hide to Background" in result.stdout
    assert "Exit" in result.stdout


def test_cli_daemon_help_exposes_lifecycle_commands():
    result = subprocess.run(
        [sys.executable, "-m", "letitbe_router.cli", "daemon", "--help"],
        text=True,
        capture_output=True,
        check=True,
    )

    assert "start" in result.stdout
    assert "stop" in result.stdout
    assert "status" in result.stdout
