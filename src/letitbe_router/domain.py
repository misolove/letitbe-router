"""Domain objects owned by Letitbe Router.

Do not expose upstream semantic-router objects from public APIs.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RouteSpec:
    """A semantic route and its preferred agent candidates."""

    name: str
    utterances: tuple[str, ...]
    candidates: tuple[str, ...]


@dataclass(frozen=True)
class RouteDecision:
    """Normalized route result returned by Letitbe Router."""

    text: str
    route: str | None
    candidates: list[str] = field(default_factory=list)
    score: float | None = None
    reason: str = "semantic route matched"
