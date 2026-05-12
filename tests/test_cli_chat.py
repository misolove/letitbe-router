import os
import subprocess
import sys


def test_cli_chat_uses_default_chat_agent_without_routing():
    env = os.environ.copy()
    env["LETITBE_ROUTER_ENABLE_TEST_AGENT"] = "1"
    env["LETITBE_ROUTER_DEFAULT_CHAT_AGENT"] = "test-echo"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "letitbe_router.cli",
            "chat",
            "안녕",
            "--timeout",
            "5",
        ],
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )

    assert "mode: chat" in result.stdout
    assert "route: chat" in result.stdout
    assert "agent: test-echo" in result.stdout
    assert "안녕" in result.stdout
    assert "RuntimeWarning" not in result.stderr


def test_cli_chat_dry_run_prints_command():
    env = os.environ.copy()
    env["LETITBE_ROUTER_ENABLE_TEST_AGENT"] = "1"
    env["LETITBE_ROUTER_DEFAULT_CHAT_AGENT"] = "test-echo"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "letitbe_router.cli",
            "chat",
            "hello",
            "--dry-run",
        ],
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )

    assert "mode: chat" in result.stdout
    assert "route: chat" in result.stdout
    assert "agent: test-echo" in result.stdout
    assert "command:" in result.stdout
    assert "dry_run: true" in result.stdout


def test_cli_chat_can_override_agent():
    env = os.environ.copy()
    env["LETITBE_ROUTER_ENABLE_TEST_AGENT"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "letitbe_router.cli",
            "chat",
            "hello override",
            "--agent",
            "test-echo",
            "--timeout",
            "5",
        ],
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )

    assert "agent: test-echo" in result.stdout
    assert "hello override" in result.stdout
