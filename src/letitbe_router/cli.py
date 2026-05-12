"""Command-line interface for Letitbe Router."""

from __future__ import annotations

import argparse
import json
import os
import shlex
import sys
import urllib.error
import urllib.request

from letitbe_router import __version__
from letitbe_router.adapters import list_adapters, render_adapter
from letitbe_router.agents import DEFAULT_AGENTS, CliAgent, agents_from_config
from letitbe_router.config import (
    ConfigError,
    config_path,
    load_config,
    sample_config_json,
    write_sample_config,
)
from letitbe_router.daemon import render_daemon_status, start_daemon, stop_daemon
from letitbe_router.executor import Executor, build_command
from letitbe_router.router import LetitbeRouter
from letitbe_router.server import serve
from letitbe_router.tui import render_tui_menu

SMOKE_CASES = (
    "please fix the failing pytest and update the code",
    "compare semantic-router docs with other model routers",
    "review this plan and identify architectural risks",
)
DEFAULT_CHAT_AGENT = "claude-code"


def _positive_int(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("positive integer required")
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="lr", description="Letitbe Router CLI")
    parser.add_argument("--version", action="store_true", help="show package version")
    subparsers = parser.add_subparsers(dest="command")

    route_parser = subparsers.add_parser("route", help="route text without executing an agent")
    route_parser.add_argument("text", nargs="+", help="text to route")

    run_parser = subparsers.add_parser("run", help="route text and execute the selected CLI agent")
    run_parser.add_argument("text", nargs="+", help="text to route and execute")
    run_parser.add_argument(
        "--agent",
        help="override the routed agent",
    )
    run_parser.add_argument(
        "--fallback-agent",
        help="agent to use when no semantic route matches",
    )
    _add_execution_options(run_parser)

    chat_parser = subparsers.add_parser("chat", help="execute a general chat prompt")
    chat_parser.add_argument("text", nargs="+", help="chat text to execute")
    chat_parser.add_argument(
        "--agent",
        help=f"chat agent override (default: {DEFAULT_CHAT_AGENT})",
    )
    _add_execution_options(chat_parser)

    subparsers.add_parser("smoke", help="run deterministic offline routing smoke test")

    serve_parser = subparsers.add_parser(
        "serve", help="run OpenAI-compatible HTTP API server"
    )
    serve_parser.add_argument("--host", default="127.0.0.1", help="bind host")
    serve_parser.add_argument("--port", type=_positive_int, default=20128, help="bind port")
    serve_parser.add_argument(
        "--timeout",
        type=_positive_int,
        default=120,
        help="agent execution timeout in seconds",
    )
    serve_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="return selected command without executing agents",
    )

    status_parser = subparsers.add_parser("status", help="check OpenAI API server health")
    status_parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:20128",
        help="server base URL",
    )

    tui_parser = subparsers.add_parser("tui", help="show 9router-style terminal menu")
    tui_parser.add_argument(
        "--base-url",
        default="http://localhost:20128",
        help="server base URL shown in the menu",
    )
    tui_parser.add_argument("--once", action="store_true", help="render menu once and exit")

    daemon_parser = subparsers.add_parser("daemon", help="manage background API server")
    daemon_subparsers = daemon_parser.add_subparsers(dest="daemon_command")
    daemon_start = daemon_subparsers.add_parser("start", help="start background API server")
    daemon_start.add_argument("--host", default="127.0.0.1", help="bind host")
    daemon_start.add_argument("--port", type=_positive_int, default=20128, help="bind port")
    daemon_start.add_argument("--timeout", type=_positive_int, default=120, help="agent timeout")
    daemon_start.add_argument("--dry-run", action="store_true", help="dry-run agent execution")
    daemon_stop = daemon_subparsers.add_parser("stop", help="stop background API server")
    daemon_stop.set_defaults(_daemon_stop=True)
    daemon_status = daemon_subparsers.add_parser("status", help="show background API server status")
    daemon_status.add_argument(
        "--base-url",
        default="http://127.0.0.1:20128",
        help="server base URL",
    )

    config_parser = subparsers.add_parser("config", help="inspect letitbe-router config")
    config_subparsers = config_parser.add_subparsers(dest="config_command")
    config_subparsers.add_parser("path", help="print config path")
    config_subparsers.add_parser("sample", help="print sample config JSON")
    config_subparsers.add_parser("show", help="print effective config JSON")
    config_init = config_subparsers.add_parser("init", help="write sample config JSON")
    config_init.add_argument("--force", action="store_true", help="overwrite existing config")

    adapter_parser = subparsers.add_parser("adapter", help="render dry-run integration snippets")
    adapter_subparsers = adapter_parser.add_subparsers(dest="adapter_command")
    adapter_subparsers.add_parser("list", help="list known adapter targets")
    adapter_render = adapter_subparsers.add_parser(
        "render", help="render a dry-run adapter snippet"
    )
    adapter_render.add_argument("target", help="adapter target name")

    args = parser.parse_args(argv)
    if args.version:
        print(__version__)
        return 0

    if args.command is None:
        parser.print_help()
        return 0

    if args.command == "config":
        return _handle_config(args, parser)

    if args.command == "adapter":
        return _handle_adapter(args, parser)

    if args.command == "serve":
        serve(host=args.host, port=args.port, timeout_seconds=args.timeout, dry_run=args.dry_run)
        return 0

    if args.command == "status":
        return _handle_status(args.base_url)

    if args.command == "tui":
        return _handle_tui(args.base_url, once=args.once)

    if args.command == "daemon":
        return _handle_daemon(args)

    try:
        agents = _available_agents()
    except ConfigError as exc:
        print(f"config error: {exc}")
        return 2

    if args.command == "chat":
        text = " ".join(args.text)
        agent_name = args.agent or _default_chat_agent(agents)
        agent = _resolve_agent(agents, agent_name)
        if agent is None:
            print(f"error: unknown or disabled agent: {agent_name}")
            print(f"available: {', '.join(sorted(agents)) or '-'}")
            return 2
        return _execute_agent(
            text=text,
            route_label="chat",
            agent=agent,
            timeout=args.timeout,
            dry_run=args.dry_run,
            mode="chat",
        )

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
        route_label = decision.route
        reason = None
        if agent_name is None and args.fallback_agent:
            agent_name = args.fallback_agent
            route_label = "fallback"
            reason = "no route matched; using fallback agent"
        if agent_name is None:
            print(f"text: {text}")
            print(f"route: {decision.route}")
            print("agent: -")
            print("returncode: 2")
            print("error: no routed agent; pass --agent or --fallback-agent to override")
            return 2

        agent = _resolve_agent(agents, agent_name)
        if agent is None:
            print(f"text: {text}")
            print(f"route: {route_label}")
            print(f"agent: {agent_name}")
            print("returncode: 2")
            print(f"error: unknown or disabled agent: {agent_name}")
            print(f"available: {', '.join(sorted(agents)) or '-'}")
            return 2
        return _execute_agent(
            text=text,
            route_label=route_label,
            agent=agent,
            timeout=args.timeout,
            dry_run=args.dry_run,
            reason=reason,
        )

    if args.command == "smoke":
        for text in SMOKE_CASES:
            decision = router.route(text)
            _print_decision(decision)
        print("SMOKE_OK")
        return 0

    parser.print_help()
    return 0


def _handle_config(args, parser: argparse.ArgumentParser) -> int:
    if args.config_command is None:
        parser.parse_args(["config", "--help"])
        return 0
    if args.config_command == "path":
        print(config_path())
        return 0
    if args.config_command == "sample":
        print(sample_config_json(), end="")
        return 0
    if args.config_command == "show":
        import json

        try:
            effective_config = load_config()
        except ConfigError as exc:
            print(f"config error: {exc}")
            return 2
        print(json.dumps(effective_config.to_dict(), ensure_ascii=False, indent=2))
        return 0
    if args.config_command == "init":
        try:
            written = write_sample_config(force=args.force)
        except FileExistsError as exc:
            print(f"error: config already exists: {exc.filename}; pass --force to overwrite")
            return 2
        print(f"wrote: {written}")
        return 0
    return 2


def _handle_adapter(args, parser: argparse.ArgumentParser) -> int:
    if args.adapter_command is None:
        parser.parse_args(["adapter", "--help"])
        return 0
    if args.adapter_command == "list":
        for adapter in list_adapters():
            print(f"{adapter.target}: {adapter.description}")
        return 0
    if args.adapter_command == "render":
        try:
            print(render_adapter(args.target), end="")
        except KeyError as exc:
            print(f"error: {exc}")
            return 2
        return 0
    return 2


def _handle_status(base_url: str) -> int:
    url = base_url.rstrip("/") + "/health"
    try:
        with urllib.request.urlopen(url, timeout=5) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (OSError, json.JSONDecodeError, urllib.error.URLError) as exc:
        print("status: unavailable")
        print(f"error: {exc}")
        return 2
    print(f"status: {payload.get('status', 'unknown')}")
    print(f"version: {payload.get('version', '-')}")
    print(f"url: {base_url.rstrip('/')}")
    return 0


def _handle_tui(base_url: str, *, once: bool = False) -> int:
    print(render_tui_menu(base_url=base_url), end="")
    if once or not sys.stdin.isatty():
        return 0
    while True:
        choice = input("Select [1=status, 2=terminal, 3=background, 4=exit]: ").strip()
        if choice == "1":
            _handle_status(base_url)
        elif choice == "2":
            print("Terminal UI shell is not expanded yet; use lr chat/run directly.")
        elif choice == "3":
            host_port = base_url.removeprefix("http://").removeprefix("https://")
            host, _, port_text = host_port.partition(":")
            port = int(port_text or "20128")
            try:
                pid, log_file = start_daemon(host=host or "127.0.0.1", port=port)
            except RuntimeError as exc:
                print(f"error: {exc}")
            else:
                print(f"started: pid {pid}")
                print(f"log: {log_file}")
        elif choice == "4" or choice.lower() in {"q", "quit", "exit"}:
            return 0
        else:
            print("unknown choice")


def _handle_daemon(args) -> int:
    if args.daemon_command is None:
        print("usage: lr daemon {start,stop,status} ...")
        return 0
    if args.daemon_command == "start":
        try:
            pid, log_file = start_daemon(
                host=args.host,
                port=args.port,
                timeout_seconds=args.timeout,
                dry_run=args.dry_run,
            )
        except RuntimeError as exc:
            print(f"error: {exc}")
            return 2
        print("status: started")
        print(f"pid: {pid}")
        print(f"url: http://{args.host}:{args.port}")
        print(f"log_file: {log_file}")
        return 0
    if args.daemon_command == "stop":
        pid = stop_daemon()
        if pid is None:
            print("status: stopped")
            print("pid: -")
        else:
            print("status: stopped")
            print(f"pid: {pid}")
        return 0
    if args.daemon_command == "status":
        print(render_daemon_status(base_url=args.base_url))
        return 0
    return 2


def _add_execution_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="print the selected command without executing it",
    )
    parser.add_argument(
        "--timeout",
        type=_positive_int,
        default=120,
        help="execution timeout in seconds",
    )


def _available_agents() -> dict[str, CliAgent]:
    agents = agents_from_config(load_config())
    if not agents:
        agents = dict(DEFAULT_AGENTS)
    if os.environ.get("LETITBE_ROUTER_ENABLE_TEST_AGENT") == "1":
        agents["test-echo"] = CliAgent(
            name="test-echo",
            command=("python", "-c", "import sys; print(sys.argv[1])", "{prompt}"),
            description="Test-only echo command for CLI integration tests.",
        )
    return agents


def _default_chat_agent(agents: dict[str, CliAgent]) -> str:
    configured = os.environ.get("LETITBE_ROUTER_DEFAULT_CHAT_AGENT") or load_config().defaults.get(
        "chat_agent", DEFAULT_CHAT_AGENT
    )
    if configured not in agents:
        return DEFAULT_CHAT_AGENT
    return configured


def _resolve_agent(agents: dict[str, CliAgent], name: str | None) -> CliAgent | None:
    if name is None:
        return None
    return agents.get(name)


def _first_candidate(decision) -> str | None:
    return decision.candidates[0] if decision.candidates else None


def _execute_agent(
    *,
    text: str,
    route_label: str | None,
    agent: CliAgent,
    timeout: int,
    dry_run: bool,
    mode: str | None = None,
    reason: str | None = None,
) -> int:
    command = build_command(agent.command, text)
    if mode:
        print(f"mode: {mode}")
    print(f"text: {text}")
    print(f"route: {route_label}")
    print(f"agent: {agent.name}")
    if reason:
        print(f"reason: {reason}")
    print(f"command: {shlex.join(command)}")
    if dry_run:
        print("dry_run: true")
        return 0

    result = Executor(timeout_seconds=timeout).run(agent, text)
    print(f"returncode: {result.returncode}")
    print(f"timed_out: {str(result.timed_out).lower()}")
    if result.stdout:
        print("--- stdout ---")
        print(result.stdout.rstrip())
    if result.stderr:
        print("--- stderr ---")
        print(result.stderr.rstrip())
    return result.returncode


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
