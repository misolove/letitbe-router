import os
import subprocess
import sys


def test_cli_run_dry_run_prints_command_without_executing():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "letitbe_router.cli",
            "run",
            "fix pytest and update code",
            "--dry-run",
        ],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "route: code_worker" in result.stdout
    assert "agent: codex-cli" in result.stdout
    assert "command:" in result.stdout
    assert "dry_run: true" in result.stdout


def test_cli_run_no_route_without_agent_exits_cleanly():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "letitbe_router.cli",
            "run",
            "what should I eat for dinner",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "no routed agent" in result.stdout


def test_cli_run_rejects_non_positive_timeout():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "letitbe_router.cli",
            "run",
            "fix pytest",
            "--timeout",
            "0",
        ],
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 2
    assert "positive integer" in result.stderr


def test_cli_run_non_ascii_no_route_does_not_emit_runtime_warning():
    env = os.environ.copy()
    env["LETITBE_ROUTER_ENABLE_TEST_AGENT"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "letitbe_router.cli",
            "run",
            "안녕",
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

    assert "RuntimeWarning" not in result.stderr
    assert "invalid value encountered" not in result.stderr
    assert "안녕" in result.stdout


def test_cli_run_can_override_agent_with_test_echo():
    env = os.environ.copy()
    env["LETITBE_ROUTER_ENABLE_TEST_AGENT"] = "1"
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "letitbe_router.cli",
            "run",
            "hello from cli",
            "--agent",
            "test-echo",
            "--timeout",
            "5",
        ],
        check=True,
        text=True,
        capture_output=True,
        env=env,
    )

    assert "agent: test-echo" in result.stdout
    assert "returncode: 0" in result.stdout
    assert "hello from cli" in result.stdout
