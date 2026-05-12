"""Agent command definitions for CLI executor bridge."""

from __future__ import annotations

from dataclasses import dataclass

from letitbe_router.config import RouterConfig


@dataclass(frozen=True)
class CliAgent:
    """A non-interactive CLI agent command template."""

    name: str
    command: tuple[str, ...]
    description: str


def agents_from_config(config: RouterConfig) -> dict[str, CliAgent]:
    """Return enabled CLI agents from router config."""

    return {
        name: CliAgent(name=name, command=agent.command, description=agent.description)
        for name, agent in config.agents.items()
        if agent.enabled
    }


DEFAULT_AGENTS: dict[str, CliAgent] = agents_from_config(RouterConfig.sample())
