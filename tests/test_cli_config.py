import os
import subprocess
import sys


def test_cli_config_path_ignores_invalid_config(tmp_path):
    bad_config = tmp_path / "bad.json"
    bad_config.write_text("{not-json", encoding="utf-8")
    env = os.environ.copy()
    env["LETITBE_ROUTER_CONFIG"] = str(bad_config)

    result = subprocess.run(
        [sys.executable, "-m", "letitbe_router.cli", "config", "path"],
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )

    assert str(bad_config) in result.stdout


def test_cli_chat_reports_invalid_config_without_traceback(tmp_path):
    bad_config = tmp_path / "bad.json"
    bad_config.write_text("{not-json", encoding="utf-8")
    env = os.environ.copy()
    env["LETITBE_ROUTER_CONFIG"] = str(bad_config)

    result = subprocess.run(
        [sys.executable, "-m", "letitbe_router.cli", "chat", "hello"],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    assert result.returncode == 2
    assert "config error:" in result.stdout
    assert "Traceback" not in result.stderr


def test_cli_config_rejects_invalid_command_schema(tmp_path):
    bad_config = tmp_path / "bad-command.json"
    bad_config.write_text(
        """
{
  "agents": {
    "bad-agent": {
      "enabled": true,
      "command": "echo {prompt}",
      "description": "bad"
    }
  }
}
""".strip(),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["LETITBE_ROUTER_CONFIG"] = str(bad_config)

    result = subprocess.run(
        [sys.executable, "-m", "letitbe_router.cli", "config", "show"],
        text=True,
        capture_output=True,
        check=False,
        env=env,
    )

    assert result.returncode == 2
    assert "agents.bad-agent.command" in result.stdout


def test_cli_configured_agent_is_available_for_chat(tmp_path):
    config_path = tmp_path / "router.json"
    config_path.write_text(
        """
{
  "defaults": {"chat_agent": "local-echo"},
  "agents": {
    "local-echo": {
      "enabled": true,
      "command": ["python", "-c", "import sys; print(sys.argv[1])", "{prompt}"],
      "description": "local echo"
    }
  }
}
""".strip(),
        encoding="utf-8",
    )
    env = os.environ.copy()
    env["LETITBE_ROUTER_CONFIG"] = str(config_path)

    result = subprocess.run(
        [sys.executable, "-m", "letitbe_router.cli", "chat", "hello configured", "--timeout", "5"],
        text=True,
        capture_output=True,
        check=True,
        env=env,
    )

    assert "agent: local-echo" in result.stdout
    assert "hello configured" in result.stdout


def test_cli_config_sample_prints_json_with_integrations():
    result = subprocess.run(
        [sys.executable, "-m", "letitbe_router.cli", "config", "sample"],
        text=True,
        capture_output=True,
        check=True,
    )

    assert '"agents"' in result.stdout
    assert '"hermes-agent"' in result.stdout
    assert '"openclaw"' in result.stdout


def test_cli_adapter_list_mentions_supported_targets():
    result = subprocess.run(
        [sys.executable, "-m", "letitbe_router.cli", "adapter", "list"],
        text=True,
        capture_output=True,
        check=True,
    )

    assert "hermes" in result.stdout
    assert "opencode" in result.stdout
    assert "openclaw" in result.stdout
    assert "codex" in result.stdout
    assert "claude-code" in result.stdout
    assert "gemini" in result.stdout


def test_cli_adapter_render_is_dry_run_only():
    result = subprocess.run(
        [sys.executable, "-m", "letitbe_router.cli", "adapter", "render", "hermes"],
        text=True,
        capture_output=True,
        check=True,
    )

    assert "target: hermes" in result.stdout
    assert "apply: false" in result.stdout
    assert "lr run" in result.stdout
