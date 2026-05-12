"""semantic-router adapter.

This module is the only place that should import upstream ``semantic_router``.
"""

from __future__ import annotations

import hashlib
import re
from typing import Any

import numpy as np
from semantic_router import Route
from semantic_router.encoders import DenseEncoder
from semantic_router.routers import SemanticRouter

from letitbe_router.domain import RouteDecision, RouteSpec


def _disable_upstream_logs() -> None:
    try:
        from semantic_router.utils.logger import logger as semantic_logger
    except Exception:
        return
    semantic_logger.disabled = True
    semantic_logger.propagate = False


_disable_upstream_logs()


class LocalHashDenseEncoder(DenseEncoder):
    """Deterministic local encoder for tests and offline smoke checks.

    This is intentionally lightweight. It verifies routing plumbing without API keys or model
    downloads; production-quality semantic matching can be added behind the same adapter later.
    """

    dims: int = 256

    def __init__(self, dims: int = 256, score_threshold: float = 0.18):
        super().__init__(name="letitbe-local-hash-dense", score_threshold=score_threshold)
        self.dims = dims

    def __call__(self, docs: list[Any]) -> list[list[float]]:
        vectors: list[list[float]] = []
        for doc in docs:
            tokens = re.findall(r"[\w+#.-]+", str(doc).lower(), flags=re.UNICODE)
            if not tokens:
                tokens = ["__empty__"]
            vec = np.zeros(self.dims, dtype=np.float32)
            for token in tokens:
                idx = _bucket(token, self.dims)
                vec[idx] += 1.0

            hints = {
                "code": ("code", "pytest", "unit", "test", "implement", "fix", "refactor", "debug"),
                "research": (
                    "research",
                    "docs",
                    "documentation",
                    "compare",
                    "sources",
                    "web",
                    "libraries",
                ),
                "review": (
                    "review",
                    "risks",
                    "risk",
                    "architecture",
                    "critique",
                    "adversarial",
                    "design",
                ),
            }
            token_set = set(tokens)
            for group, words in hints.items():
                if token_set.intersection(words):
                    vec[_bucket("hint:" + group, self.dims)] += 3.0

            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec.tolist())
        return vectors


def _bucket(value: str, dims: int) -> int:
    return int(hashlib.sha256(value.encode()).hexdigest()[:8], 16) % dims


class SemanticRouterBackend:
    """Adapter that converts Letitbe route specs to semantic-router routes."""

    def __init__(self, routes: tuple[RouteSpec, ...]):
        self._route_specs = {route.name: route for route in routes}
        upstream_routes = [
            Route(name=route.name, utterances=list(route.utterances)) for route in routes
        ]
        self._router = SemanticRouter(
            encoder=LocalHashDenseEncoder(),
            routes=upstream_routes,
            auto_sync="local",
        )

    def route(self, text: str) -> RouteDecision:
        choice = self._router(text)
        route_name = getattr(choice, "name", None) if choice else None
        if route_name not in self._route_specs:
            return RouteDecision(
                text=text,
                route=None,
                candidates=[],
                score=None,
                reason="no semantic route matched",
            )

        spec = self._route_specs[route_name]
        return RouteDecision(
            text=text,
            route=route_name,
            candidates=list(spec.candidates),
            score=getattr(choice, "similarity_score", None),
        )
