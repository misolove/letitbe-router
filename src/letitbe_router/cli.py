"""Command-line interface for Letitbe Router."""

from __future__ import annotations

import argparse

from letitbe_router import __version__
from letitbe_router.router import LetitbeRouter

SMOKE_CASES = (
    "please fix the failing pytest and update the code",
    "compare semantic-router docs with other model routers",
    "review this plan and identify architectural risks",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lr", description="Letitbe Router CLI")
    parser.add_argument("--version", action="store_true", help="show package version")
    subparsers = parser.add_subparsers(dest="command")

    route_parser = subparsers.add_parser("route", help="route text without executing an agent")
    route_parser.add_argument("text", nargs="+", help="text to route")

    subparsers.add_parser("smoke", help="run deterministic offline routing smoke test")

    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return 0

    if args.command is None:
        parser.print_help()
        return 0

    router = LetitbeRouter.default()

    if args.command == "route":
        text = " ".join(args.text)
        decision = router.route(text)
        _print_decision(decision)
        return 0

    if args.command == "smoke":
        for text in SMOKE_CASES:
            decision = router.route(text)
            _print_decision(decision)
        print("SMOKE_OK")
        return 0

    parser.print_help()
    return 0


def _print_decision(decision):
    print(f"text: {decision.text}")
    print(f"route: {decision.route}")
    if decision.candidates:
        print(f"candidate: {decision.candidates[0]}")
        print(f"fallbacks: {', '.join(decision.candidates[1:]) or '-'}")
    else:
        print("candidate: -")
    if decision.score is not None:
        print(f"score: {decision.score:.4f}")
    print(f"reason: {decision.reason}")
    print()


if __name__ == "__main__":
    raise SystemExit(main())
