"""Command-line interface for Letitbe Router."""

from __future__ import annotations

import argparse
import os
import shlex

from letitbe_router import __version__
from letitbe_router.agents import DEFAULT_AGENTS, CliAgent
from letitbe_router.executor import Executor, build_command
from letitbe_router.router import LetitbeRouter

SMOKE_CASES = (
    "please fix the failing pytest and update the code",
    "compare semantic-router docs with other model routers",
    "review this plan and identify architectural risks",
)


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("positive integer required")
    return parsed


def main(argv: list[str] | None = None) -> int:
    agents = _available_agents()
    parser = argparse.ArgumentParser(prog="lr", description="Letitbe Router CLI")
    parser.add_argument("--version", action="store_true", help="show package version")
    subparsers = parser.add_subparsers(dest="command")

    route_parser = subparsers.add_parser("route", help="route text without executing an agent")
    route_parser.add_argument("text", nargs="+", help="text to route")

    run_parser = subparsers.add_parser("run", help="route text and execute the selected CLI agent")
    run_parser.add_argument("text", nargs="+", help="text to route and execute")
    run_parser.add_argument(
        "--agent",
        choices=sorted(agents),
        help="override the routed agent",
    )
    run_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the selected command without executing it",
    )
    run_parser.add_argument(
        "--timeout",
        type=_positive_int,
        default=120,
        help="execution timeout in seconds",
    )

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

    if args.command == "run":
        text = " ".join(args.text)
        decision = router.route(text)
        agent_name = args.agent or _first_candidate(decision)
        if agent_name is None:
            print(f"text: {text}")
            print(f"route: {decision.route}")
            print("agent: -")
            print("returncode: 2")
            print("error: no routed agent; pass --agent to override")
            return 2

        agent = agents[agent_name]
        command = build_command(agent.command, text)
        print(f"text: {text}")
        print(f"route: {decision.route}")
        print(f"agent: {agent.name}")
        print(f"command: {shlex.join(command)}")
        if args.dry_run:
            print("dry_run: true")
            return 0

        result = Executor(timeout_seconds=args.timeout).run(agent, text)
        print(f"returncode: {result.returncode}")
        print(f"timed_out: {str(result.timed_out).lower()}")
        if result.stdout:
            print("--- stdout ---")
            print(result.stdout.rstrip())
        if result.stderr:
            print("--- stderr ---")
            print(result.stderr.rstrip())
        return result.returncode

    if args.command == "smoke":
        for text in SMOKE_CASES:
            decision = router.route(text)
            _print_decision(decision)
        print("SMOKE_OK")
        return 0

    parser.print_help()
    return 0


def _available_agents() -> dict[str, CliAgent]:
    agents = dict(DEFAULT_AGENTS)
    if os.environ.get("LETITBE_ROUTER_ENABLE_TEST_AGENT") == "1":
        agents["test-echo"] = CliAgent(
            name="test-echo",
            command=("python", "-c", "import sys; print(sys.argv[1])", "{prompt}"),
            description="Test-only echo command for CLI integration tests.",
        )
    return agents


def _first_candidate(decision) -> str | None:
    return decision.candidates[0] if decision.candidates else None


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
