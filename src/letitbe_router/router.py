"""Public Letitbe Router facade."""

from __future__ import annotations

from letitbe_router.backends.semantic_router import SemanticRouterBackend
from letitbe_router.defaults import DEFAULT_ROUTES
from letitbe_router.domain import RouteDecision, RouteSpec


class LetitbeRouter:
    """High-level router facade used by CLI and future integrations."""

    def __init__(self, routes: tuple[RouteSpec, ...]):
        self._backend = SemanticRouterBackend(routes)

    @classmethod
    def default(cls) -> LetitbeRouter:
        return cls(DEFAULT_ROUTES)

    def route(self, text: str) -> RouteDecision:
        return self._backend.route(text)
