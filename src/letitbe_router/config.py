"""Configuration model for Letitbe Router.

The runtime config is intentionally JSON/std-lib only. It lets users prepare
adapter definitions for other agent CLIs without mutating those tools' configs.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_CONFIG_PATH = Path("~/.config/letitbe-router/config.json").expanduser()
CONFIG_ENV = "LETITBE_ROUTER_CONFIG"


class ConfigError(ValueError):
    """User-facing config error."""


@dataclass(frozen=True)
class AgentConfig:
    """Serializable CLI-agent template loaded from config."""

    enabled: bool
    command: tuple[str, ...]
    description: str


@dataclass(frozen=True)
class RouterConfig:
    """User-editable config for future multi-agent integration."""

    agents: dict[str, AgentConfig] = field(default_factory=dict)
    defaults: dict[str, str] = field(default_factory=dict)

    @classmethod
    def sample(cls) -> RouterConfig:
        return cls(
            defaults={"chat_agent": "claude-code", "fallback_agent": "claude-code"},
            agents={
                "codex-cli": AgentConfig(
                    enabled=True,
                    command=(
                        "codex",
                        "exec",
                        "--sandbox",
                        "read-only",
                        "--skip-git-repo-check",
                        "{prompt}",
                    ),
                    description="OpenAI Codex CLI in non-interactive read-only exec mode.",
                ),
                "claude-code": AgentConfig(
                    enabled=True,
                    command=(
                        "claude",
                        "--print",
                        "{prompt}",
                        "--permission-mode",
                        "plan",
                        "--max-turns",
                        "3",
                    ),
                    description="Claude Code CLI in print mode with plan permissions.",
                ),
                "gemini-cli": AgentConfig(
                    enabled=True,
                    command=("gemini", "--prompt", "{prompt}", "--approval-mode", "plan"),
                    description="Gemini CLI in headless plan/read-only mode.",
                ),
                "hermes-agent": AgentConfig(
                    enabled=False,
                    command=("hermes", "chat", "-q", "{prompt}", "--quiet"),
                    description="Hermes Agent one-shot chat adapter; disabled until opted in.",
                ),
                "opencode": AgentConfig(
                    enabled=False,
                    command=("opencode", "run", "{prompt}"),
                    description="OpenCode one-shot run adapter; disabled until opted in.",
                ),
                "openclaw": AgentConfig(
                    enabled=False,
                    command=("openclaw", "run", "{prompt}"),
                    description=(
                        "OpenClaw placeholder adapter; "
                        "adjust command to local install before enabling."
                    ),
                ),
            },
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "defaults": dict(self.defaults),
            "agents": {
                name: {
                    "enabled": agent.enabled,
                    "command": list(agent.command),
                    "description": agent.description,
                }
                for name, agent in self.agents.items()
            },
        }


def config_path(explicit: str | Path | None = None) -> Path:
    if explicit is not None:
        return Path(explicit).expanduser()
    if env_path := os.environ.get(CONFIG_ENV):
        return Path(env_path).expanduser()
    return DEFAULT_CONFIG_PATH


def load_config(path: str | Path | None = None) -> RouterConfig:
    resolved = config_path(path)
    base = RouterConfig.sample()
    if not resolved.exists():
        return base

    try:
        data = json.loads(resolved.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"invalid JSON in {resolved}: {exc.msg}") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"config root must be an object: {resolved}")

    defaults = dict(base.defaults)
    defaults.update(_string_dict(data.get("defaults", {})))

    agents = dict(base.agents)
    raw_agents = data.get("agents", {})
    if not isinstance(raw_agents, dict):
        raise ConfigError("agents must be an object")
    for name, raw_agent in raw_agents.items():
        if not isinstance(raw_agent, dict):
            raise ConfigError(f"agents.{name} must be an object")
        base_agent = agents.get(name)
        command = _command_tuple(
            raw_agent.get("command", base_agent.command if base_agent else None),
            field=f"agents.{name}.command",
        )
        agents[name] = AgentConfig(
            enabled=bool(raw_agent.get("enabled", base_agent.enabled if base_agent else False)),
            command=command,
            description=str(
                raw_agent.get("description", base_agent.description if base_agent else "")
            ),
        )
    return RouterConfig(agents=agents, defaults=defaults)


def sample_config_json() -> str:
    return json.dumps(RouterConfig.sample().to_dict(), ensure_ascii=False, indent=2) + "\n"


def write_sample_config(path: str | Path | None = None, *, force: bool = False) -> Path:
    resolved = config_path(path)
    if resolved.exists() and not force:
        raise FileExistsError(resolved)
    resolved.parent.mkdir(parents=True, exist_ok=True)
    resolved.write_text(sample_config_json(), encoding="utf-8")
    return resolved


def _command_tuple(value: Any, *, field: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ConfigError(f"{field} must be a non-empty list of strings")
    if not value:
        raise ConfigError(f"{field} must be a non-empty list of strings")
    if not all(isinstance(part, str) for part in value):
        raise ConfigError(f"{field} must contain only strings")
    if "{prompt}" not in value:
        raise ConfigError(f"{field} must include a {{prompt}} placeholder")
    return tuple(value)


def _string_dict(value: Any) -> dict[str, str]:
    if not isinstance(value, dict):
        return {}
    return {str(k): str(v) for k, v in value.items()}
