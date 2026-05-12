from letitbe_router import __version__
from letitbe_router.domain import RouteDecision
from letitbe_router.router import LetitbeRouter


def test_package_version_is_available():
    assert __version__ == "0.1.0"


def test_default_router_routes_code_research_and_review_intents():
    router = LetitbeRouter.default()

    cases = [
        ("please fix the failing pytest and update the code", "code_worker", "codex-cli"),
        ("compare semantic-router docs with other model routers", "research", "gemini-cli"),
        ("review this plan and identify architectural risks", "review", "claude-code"),
    ]

    for text, expected_route, expected_agent in cases:
        decision = router.route(text)
        assert isinstance(decision, RouteDecision)
        assert decision.route == expected_route
        assert decision.candidates[0] == expected_agent
        assert decision.score is None or decision.score >= 0


def test_default_router_returns_no_route_for_unrelated_text():
    router = LetitbeRouter.default()

    decision = router.route("what should I eat for dinner?")

    assert decision.route is None
    assert decision.candidates == []
    assert decision.reason == "no semantic route matched"
