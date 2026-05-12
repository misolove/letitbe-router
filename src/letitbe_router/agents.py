"""Agent command definitions for CLI executor bridge."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CliAgent:
    """A non-interactive CLI agent command template."""

    name: str
    command: tuple[str, ...]
    description: str


DEFAULT_AGENTS: dict[str, CliAgent] = {
    "codex-cli": CliAgent(
        name="codex-cli",
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
    "gemini-cli": CliAgent(
        name="gemini-cli",
        command=("gemini", "--prompt", "{prompt}", "--approval-mode", "plan"),
        description="Gemini CLI in headless plan/read-only mode.",
    ),
    "claude-code": CliAgent(
        name="claude-code",
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
}
