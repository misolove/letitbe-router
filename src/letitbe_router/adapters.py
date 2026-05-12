"""Dry-run adapter rendering for external agent surfaces."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AdapterTemplate:
    target: str
    description: str
    snippet: str


ADAPTER_TEMPLATES: dict[str, AdapterTemplate] = {
    "hermes": AdapterTemplate(
        target="hermes",
        description="Hermes Agent wrapper idea. Do not mutate ~/.hermes/config.yaml automatically.",
        snippet="""# Example only: create a Hermes profile/alias that delegates prompts to lr.
# Actual integration can later use a plugin, slash command, or profile alias.
hermes chat -q 'Use lr for agent selection: lr run "<prompt>" --dry-run'
""",
    ),
    "opencode": AdapterTemplate(
        target="opencode",
        description="OpenCode one-shot adapter idea.",
        snippet="""# Enable the opencode agent in ~/.config/letitbe-router/config.json, then:
lr chat "implement a small refactor" --agent opencode --dry-run
""",
    ),
    "openclaw": AdapterTemplate(
        target="openclaw",
        description=(
            "OpenClaw placeholder adapter. "
            "Adjust the command for the local OpenClaw binary before enabling."
        ),
        snippet="""# Enable and edit the openclaw command in config.json, then:
lr chat "review this repository" --agent openclaw --dry-run
""",
    ),
    "codex": AdapterTemplate(
        target="codex",
        description="Codex CLI adapter already enabled as codex-cli.",
        snippet="""lr run "fix pytest and update code" --agent codex-cli --dry-run
""",
    ),
    "claude-code": AdapterTemplate(
        target="claude-code",
        description="Claude Code adapter already enabled as claude-code.",
        snippet="""lr chat "안녕" --agent claude-code --dry-run
""",
    ),
    "gemini": AdapterTemplate(
        target="gemini",
        description="Gemini CLI adapter already enabled as gemini-cli.",
        snippet="""lr run "compare docs and summarize" --agent gemini-cli --dry-run
""",
    ),
}


def list_adapters() -> list[AdapterTemplate]:
    return [ADAPTER_TEMPLATES[name] for name in sorted(ADAPTER_TEMPLATES)]


def render_adapter(target: str) -> str:
    if target not in ADAPTER_TEMPLATES:
        known = ", ".join(sorted(ADAPTER_TEMPLATES))
        raise KeyError(f"unknown adapter target: {target}; known: {known}")
    adapter = ADAPTER_TEMPLATES[target]
    return (
        f"target: {adapter.target}\n"
        "apply: false\n"
        f"description: {adapter.description}\n"
        "--- snippet ---\n"
        f"{adapter.snippet.rstrip()}\n"
    )
