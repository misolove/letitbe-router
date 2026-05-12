import json
import subprocess
import sys
import threading
import urllib.request
from http.server import ThreadingHTTPServer

from letitbe_router.server import make_handler


def _serve(handler_class):
    server = ThreadingHTTPServer(("127.0.0.1", 0), handler_class)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def test_cli_status_reads_health_endpoint(tmp_path, monkeypatch):
    monkeypatch.setenv("LETITBE_ROUTER_CONFIG", str(tmp_path / "missing.json"))
    server, base_url = _serve(make_handler(timeout_seconds=5))
    try:
        result = subprocess.run(
            [sys.executable, "-m", "letitbe_router.cli", "status", "--base-url", base_url],
            text=True,
            capture_output=True,
            check=True,
        )
    finally:
        server.shutdown()
        server.server_close()

    assert "status: ok" in result.stdout
    assert "version:" in result.stdout


def test_cli_serve_help_exposes_openai_api_options():
    result = subprocess.run(
        [sys.executable, "-m", "letitbe_router.cli", "serve", "--help"],
        text=True,
        capture_output=True,
        check=True,
    )

    assert "--host" in result.stdout
    assert "--port" in result.stdout
    assert "--timeout" in result.stdout


def test_cli_server_openai_api_smoke(tmp_path, monkeypatch):
    config_path = tmp_path / "router.json"
    config_path.write_text(
        """
{
  "defaults": {"chat_agent": "test-echo", "fallback_agent": "test-echo"},
  "agents": {
    "test-echo": {
      "enabled": true,
      "command": ["python", "-c", "import sys; print(sys.argv[1])", "{prompt}"],
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
        request = urllib.request.Request(
            f"{base_url}/v1/chat/completions",
            data=json.dumps(
                {
                    "model": "agent/test-echo",
                    "messages": [{"role": "user", "content": "hello api"}],
                }
            ).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            body = json.loads(response.read().decode("utf-8"))
    finally:
        server.shutdown()
        server.server_close()

    assert body["choices"][0]["message"]["content"].strip() == "hello api"
