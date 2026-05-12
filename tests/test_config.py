import json

from letitbe_router.config import AgentConfig, RouterConfig, load_config


def test_load_config_merges_user_enabled_agent(tmp_path):
    config_path = tmp_path / "letitbe-router.json"
    config_path.write_text(
        json.dumps(
            {
                "agents": {
                    "hermes-agent": {
                        "enabled": True,
                        "command": ["hermes", "chat", "-q", "{prompt}"],
                        "description": "Hermes one-shot chat",
                    }
                },
                "defaults": {"chat_agent": "hermes-agent"},
            }
        ),
        encoding="utf-8",
    )

    config = load_config(config_path)

    assert config.defaults["chat_agent"] == "hermes-agent"
    assert config.agents["hermes-agent"] == AgentConfig(
        enabled=True,
        command=("hermes", "chat", "-q", "{prompt}"),
        description="Hermes one-shot chat",
    )


def test_sample_config_contains_future_integration_targets():
    config = RouterConfig.sample()

    expected = {"hermes-agent", "opencode", "openclaw", "codex-cli", "claude-code", "gemini-cli"}

    assert expected.issubset(config.agents)
    assert config.agents["openclaw"].enabled is False
    assert "{prompt}" in config.agents["hermes-agent"].command
