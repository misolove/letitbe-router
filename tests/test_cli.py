import subprocess
import sys

import letitbe_router.cli as cli


def test_cli_smoke_outputs_smoke_ok():
    result = subprocess.run(
        [sys.executable, "-m", "letitbe_router.cli", "smoke"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "SMOKE_OK" in result.stdout
    assert "code_worker" in result.stdout
    assert "research" in result.stdout
    assert "review" in result.stdout
    assert result.stderr == ""


def test_cli_route_outputs_selected_route():
    result = subprocess.run(
        [sys.executable, "-m", "letitbe_router.cli", "route", "fix pytest and update code"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "route: code_worker" in result.stdout
    assert "candidate: codex-cli" in result.stdout


def test_cli_help_does_not_initialize_router_or_warn():
    result = subprocess.run(
        [sys.executable, "-m", "letitbe_router.cli"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert "Letitbe Router CLI" in result.stdout
    assert result.stderr == ""


def test_cli_help_does_not_create_router(monkeypatch, capsys):
    def fail_if_called():
        raise AssertionError("router should not be initialized for help output")

    monkeypatch.setattr(cli.LetitbeRouter, "default", fail_if_called)

    assert cli.main([]) == 0
    captured = capsys.readouterr()
    assert "Letitbe Router CLI" in captured.out


def test_cli_version_outputs_package_version_without_warn():
    result = subprocess.run(
        [sys.executable, "-m", "letitbe_router.cli", "--version"],
        check=True,
        text=True,
        capture_output=True,
    )

    assert result.stdout.strip() == "0.1.0"
    assert result.stderr == ""
