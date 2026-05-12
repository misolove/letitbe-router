import json
import threading
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer

from letitbe_router.server import LetitbeOpenAIHandler, make_handler


def _serve(handler_class):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_class)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def _post_json(url, payload):
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def _get_json(url):
    with urllib.request.urlopen(url, timeout=10) as response:
        return response.status, json.loads(response.read().decode("utf-8"))


def test_openai_chat_completions_executes_configured_agent(tmp_path, monkeypatch):
    config_path = tmp_path / "router.json"
    config_path.write_text(
        """
{
  "defaults": {"chat_agent": "test-echo", "fallback_agent": "test-echo"},
  "agents": {
    "test-echo": {
      "enabled": true,
      "command": ["python", "-c", "import sys; print('ECHO:' + sys.argv[1])", "{prompt}"],
      "description": "test echo"
    }
  }
}
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("LETITBE_ROUTER_CONFIG", str(config_path))
    handler = make_handler(timeout_seconds=5)
    server, base_url = _serve(handler)
    try:
        status, body = _post_json(
            f"{base_url}/v1/chat/completions",
            {
                "model": "agent/test-echo",
                "messages": [{"role": "user", "content": "hello"}],
            },
        )
    finally:
        server.shutdown()
        server.server_close()

    assert status == 200
    assert body["object"] == "chat.completion"
    assert body["model"] == "agent/test-echo"
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert body["choices"][0]["message"]["content"].strip() == "ECHO:hello"
    assert body["lr"]["agent"] == "test-echo"
    assert body["lr"]["returncode"] == 0


def test_openai_models_exposes_lr_prefixed_names(tmp_path, monkeypatch):
    config_path = tmp_path / "router.json"
    config_path.write_text(
        """
{
  "agents": {
    "test-echo": {
      "enabled": true,
      "command": ["python", "-c", "print('ok')", "{prompt}"],
      "description": "enabled"
    }
  }
}
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("LETITBE_ROUTER_CONFIG", str(config_path))
    server, base_url = _serve(make_handler(timeout_seconds=5))
    try:
        status, body = _get_json(f"{base_url}/v1/models")
    finally:
        server.shutdown()
        server.server_close()

    model_ids = {item["id"] for item in body["data"]}
    assert status == 200
    assert "lr" in model_ids
    assert "lr/auto" in model_ids
    assert "lr/test-echo" in model_ids
    assert "letitbe-router" in model_ids
    assert "agent/test-echo" in model_ids


def test_openai_chat_completions_accepts_lr_agent_model(tmp_path, monkeypatch):
    config_path = tmp_path / "router.json"
    config_path.write_text(
        """
{
  "agents": {
    "test-echo": {
      "enabled": true,
      "command": ["python", "-c", "import sys; print('LR:' + sys.argv[1])", "{prompt}"],
      "description": "test echo"
    }
  }
}
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("LETITBE_ROUTER_CONFIG", str(config_path))
    server, base_url = _serve(make_handler(timeout_seconds=5))
    try:
        status, body = _post_json(
            f"{base_url}/v1/chat/completions",
            {"model": "lr/test-echo", "messages": [{"role": "user", "content": "hello"}]},
        )
    finally:
        server.shutdown()
        server.server_close()

    assert status == 200
    assert body["model"] == "lr/test-echo"
    assert body["choices"][0]["message"]["content"].strip() == "LR:hello"
    assert body["lr"]["route"] == "direct"


def test_openai_models_lists_enabled_agents(tmp_path, monkeypatch):
    config_path = tmp_path / "router.json"
    config_path.write_text(
        """
{
  "agents": {
    "enabled-one": {
      "enabled": true,
      "command": ["python", "-c", "print('ok')", "{prompt}"],
      "description": "enabled"
    },
    "disabled-one": {
      "enabled": false,
      "command": ["python", "-c", "print('no')", "{prompt}"],
      "description": "disabled"
    }
  }
}
""".strip(),
        encoding="utf-8",
    )
    monkeypatch.setenv("LETITBE_ROUTER_CONFIG", str(config_path))
    server, base_url = _serve(make_handler(timeout_seconds=5))
    try:
        status, body = _get_json(f"{base_url}/v1/models")
    finally:
        server.shutdown()
        server.server_close()

    model_ids = {item["id"] for item in body["data"]}
    assert status == 200
    assert "letitbe-router" in model_ids
    assert "agent/enabled-one" in model_ids
    assert "agent/disabled-one" not in model_ids


def test_openai_chat_completions_rejects_streaming(tmp_path, monkeypatch):
    monkeypatch.setenv("LETITBE_ROUTER_CONFIG", str(tmp_path / "missing.json"))
    server, base_url = _serve(make_handler(timeout_seconds=5))
    try:
        request = urllib.request.Request(
            f"{base_url}/v1/chat/completions",
            data=json.dumps(
                {
                    "model": "letitbe-router",
                    "messages": [{"role": "user", "content": "hello"}],
                    "stream": True,
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            urllib.request.urlopen(request, timeout=10)
        except urllib.error.HTTPError as exc:
            status = exc.code
            body = json.loads(exc.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()

    assert status == 400
    assert body["error"]["type"] == "unsupported_feature"


def test_default_handler_type_exists():
    assert issubclass(LetitbeOpenAIHandler, object)
