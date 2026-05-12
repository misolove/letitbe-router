"""Subprocess executor for selected CLI agents."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from letitbe_router.agents import CliAgent


@dataclass(frozen=True)
class ExecutionResult:
    """Result from a CLI agent execution."""

    agent: str
    command: list[str]
    returncode: int
    stdout: str
    stderr: str
    timed_out: bool = False


def build_command(command_template: tuple[str, ...] | list[str], prompt: str) -> list[str]:
    """Substitute prompt into a command template without invoking a shell."""

    return [part.replace("{prompt}", prompt) for part in command_template]


class Executor:
    """Run CLI agents in non-interactive subprocess mode."""

    def __init__(self, timeout_seconds: int = 120, cwd: str | Path | None = None):
        self.timeout_seconds = timeout_seconds
        self.cwd = Path(cwd) if cwd else None

    def run(self, agent: CliAgent, prompt: str) -> ExecutionResult:
        command = build_command(agent.command, prompt)
        try:
            completed = subprocess.run(
                command,
                cwd=self.cwd,
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
                stdin=subprocess.DEVNULL,
            )
        except subprocess.TimeoutExpired as exc:
            return ExecutionResult(
                agent=agent.name,
                command=command,
                returncode=124,
                stdout=exc.stdout or "",
                stderr=exc.stderr or f"Timed out after {self.timeout_seconds}s",
                timed_out=True,
            )

        return ExecutionResult(
            agent=agent.name,
            command=command,
            returncode=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
        )
