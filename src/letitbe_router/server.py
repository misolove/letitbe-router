"""OpenAI-compatible HTTP gateway for Letitbe Router."""

from __future__ import annotations

import json
import time
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any

from letitbe_router import __version__
from letitbe_router.agents import CliAgent, agents_from_config
from letitbe_router.config import ConfigError, load_config
from letitbe_router.executor import Executor, build_command
from letitbe_router.router import LetitbeRouter

DEFAULT_MODEL = "letitbe-router"


class LetitbeOpenAIHandler(BaseHTTPRequestHandler):
    """Default OpenAI-compatible handler class."""

    timeout_seconds = 120
    dry_run = False
    server_version = "LetitbeRouter/0.1"

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Silence default stderr request logs; callers can wrap later."""

    def do_GET(self) -> None:  # noqa: N802
        if self.path == "/health":
            self._send_json({"status": "ok", "version": __version__})
            return
        if self.path == "/v1/models":
            try:
                agents = _available_agents()
            except ConfigError as exc:
                self._send_error(HTTPStatus.BAD_REQUEST, "config_error", str(exc))
                return
            models = [
                {"id": DEFAULT_MODEL, "object": "model", "owned_by": "letitbe-router"},
                *[
                    {"id": f"agent/{name}", "object": "model", "owned_by": "letitbe-router"}
                    for name in sorted(agents)
                ],
            ]
            self._send_json({"object": "list", "data": models})
            return
        self._send_error(HTTPStatus.NOT_FOUND, "not_found", f"unknown path: {self.path}")

    def do_POST(self) -> None:  # noqa: N802
        if self.path != "/v1/chat/completions":
            self._send_error(HTTPStatus.NOT_FOUND, "not_found", f"unknown path: {self.path}")
            return
        try:
            payload = self._read_json()
        except ValueError as exc:
            self._send_error(HTTPStatus.BAD_REQUEST, "invalid_request_error", str(exc))
            return
        if payload.get("stream") is True:
            self._send_error(
                HTTPStatus.BAD_REQUEST,
                "unsupported_feature",
                "stream=true is not supported yet; send non-streaming requests",
            )
            return
        try:
            response = chat_completion_response(
                payload,
                timeout_seconds=self.timeout_seconds,
                dry_run=self.dry_run,
            )
        except ConfigError as exc:
            self._send_error(HTTPStatus.BAD_REQUEST, "config_error", str(exc))
            return
        except LookupError as exc:
            self._send_error(HTTPStatus.BAD_REQUEST, "invalid_request_error", str(exc))
            return
        except RuntimeError as exc:
            self._send_error(HTTPStatus.BAD_GATEWAY, "agent_error", str(exc))
            return
        self._send_json(response)

    def _read_json(self) -> dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError as exc:
            raise ValueError("invalid Content-Length") from exc
        if length <= 0:
            raise ValueError("empty request body")
        raw_body = self.rfile.read(length)
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except json.JSONDecodeError as exc:
            raise ValueError(f"invalid JSON: {exc.msg}") from exc
        if not isinstance(payload, dict):
            raise ValueError("request body must be a JSON object")
        return payload

    def _send_json(self, payload: dict[str, Any], status: HTTPStatus = HTTPStatus.OK) -> None:
        encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def _send_error(self, status: HTTPStatus, error_type: str, message: str) -> None:
        self._send_json(
            {"error": {"message": message, "type": error_type, "code": None}},
            status=status,
        )


def make_handler(*, timeout_seconds: int = 120, dry_run: bool = False):
    """Create a configured HTTP handler class."""

    class ConfiguredLetitbeOpenAIHandler(LetitbeOpenAIHandler):
        pass

    ConfiguredLetitbeOpenAIHandler.timeout_seconds = timeout_seconds
    ConfiguredLetitbeOpenAIHandler.dry_run = dry_run
    return ConfiguredLetitbeOpenAIHandler


def serve(
    *,
    host: str = "127.0.0.1",
    port: int = 20128,
    timeout_seconds: int = 120,
    dry_run: bool = False,
) -> None:
    """Run a foreground OpenAI-compatible HTTP server."""

    httpd = ThreadingHTTPServer(
        (host, port), make_handler(timeout_seconds=timeout_seconds, dry_run=dry_run)
    )
    print(f"Letitbe Router OpenAI API server listening on http://{host}:{port}", flush=True)
    try:
        httpd.serve_forever()
    finally:
        httpd.server_close()


def chat_completion_response(
    payload: dict[str, Any], *, timeout_seconds: int = 120, dry_run: bool = False
) -> dict[str, Any]:
    agents = _available_agents()
    model = str(payload.get("model") or DEFAULT_MODEL)
    prompt = _messages_to_prompt(payload.get("messages"))
    agent, route_label, model_id = _select_agent(model, prompt, agents)
    command = build_command(agent.command, prompt)
    if dry_run:
        content = "dry_run: true\ncommand: " + " ".join(command)
        return _openai_response(
            model_id=model_id,
            content=content,
            agent=agent.name,
            route=route_label,
            command=command,
            returncode=0,
            dry_run=True,
        )
    result = Executor(timeout_seconds=timeout_seconds).run(agent, prompt)
    content = result.stdout.rstrip() if result.stdout else result.stderr.rstrip()
    if result.returncode != 0:
        raise RuntimeError(
            f"agent {agent.name} failed with return code {result.returncode}: {content}"
        )
    return _openai_response(
        model_id=model_id,
        content=content,
        agent=agent.name,
        route=route_label,
        command=result.command,
        returncode=result.returncode,
        dry_run=False,
    )


def _openai_response(
    *,
    model_id: str,
    content: str,
    agent: str,
    route: str | None,
    command: list[str],
    returncode: int,
    dry_run: bool,
) -> dict[str, Any]:
    return {
        "id": f"chatcmpl-lr-{int(time.time() * 1000)}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model_id,
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": content},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        "lr": {
            "route": route,
            "agent": agent,
            "command": command,
            "returncode": returncode,
            "dry_run": dry_run,
        },
    }


def _available_agents() -> dict[str, CliAgent]:
    return agents_from_config(load_config())


def _select_agent(
    model: str, prompt: str, agents: dict[str, CliAgent]
) -> tuple[CliAgent, str | None, str]:
    if model.startswith("agent/"):
        name = model.removeprefix("agent/")
        if name not in agents:
            raise LookupError(f"unknown or disabled agent: {name}")
        return agents[name], "direct", model
    if model in agents:
        return agents[model], "direct", f"agent/{model}"
    if model != DEFAULT_MODEL:
        raise LookupError(f"unknown model: {model}")

    decision = LetitbeRouter.default().route(prompt)
    candidate = decision.candidates[0] if decision.candidates else None
    if candidate and candidate in agents:
        return agents[candidate], decision.route, model

    config = load_config()
    fallback = config.defaults.get("fallback_agent") or config.defaults.get("chat_agent")
    if fallback and fallback in agents:
        return agents[fallback], "fallback", model
    raise LookupError("no routed agent and no enabled fallback agent")


def _messages_to_prompt(messages: Any) -> str:
    if not isinstance(messages, list) or not messages:
        raise LookupError("messages must be a non-empty list")
    parts: list[str] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        text = _content_to_text(content)
        if text:
            parts.append(text)
    if not parts:
        raise LookupError("messages must contain text content")
    return "\n".join(parts)


def _content_to_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, dict) and item.get("type") == "text":
                chunks.append(str(item.get("text", "")))
        return "\n".join(chunk for chunk in chunks if chunk)
    return ""
