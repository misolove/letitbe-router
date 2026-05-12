"""Default design-first route configuration for v0.1."""

from __future__ import annotations

from letitbe_router.domain import RouteSpec

DEFAULT_ROUTES: tuple[RouteSpec, ...] = (
    RouteSpec(
        name="code_worker",
        utterances=(
            "implement this feature in the repository",
            "fix failing unit tests and edit code",
            "refactor the Python module",
            "write code and run tests",
            "debug pytest failures",
        ),
        candidates=("codex-cli", "claude-code", "gemini-cli"),
    ),
    RouteSpec(
        name="research",
        utterances=(
            "research this API and summarize documentation",
            "compare these libraries from web sources",
            "find current information and explain tradeoffs",
            "read documentation and compare options",
        ),
        candidates=("gemini-cli", "claude-code", "codex-cli"),
    ),
    RouteSpec(
        name="review",
        utterances=(
            "review the architecture and find hidden risks",
            "critique this design before implementation",
            "do an adversarial code review",
            "identify architectural risks",
        ),
        candidates=("claude-code", "gemini-cli", "codex-cli"),
    ),
)
