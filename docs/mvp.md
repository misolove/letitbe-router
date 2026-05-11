# MVP Plan

The first implementation should be small, testable, and safe. It should prove the routing and scheduling model before executing real agent commands.

## v0.1: Dry-run semantic router

Goal: route text into a Letitbe route without executing anything.

Commands:

```bash
lr route "fix failing tests and update the code"
lr smoke
```

Acceptance criteria:

- `lr smoke` runs without network or API keys.
- `lr route TEXT` returns a route name, score, and candidate agents.
- No upstream `semantic_router` types leak into the public domain model.
- The adapter has contract tests for match and no-match behavior.

## v0.2: Usage collectors

Goal: read usage/limit signals for Codex CLI, Gemini CLI, and Claude Code CLI.

Commands:

```bash
lr usage
lr status
```

Acceptance criteria:

- Missing credentials produce `unknown` status, not a crash.
- Live probes are cached with `fetchedAt`.
- Failed probes do not overwrite the last successful cache.
- Every signal includes source and confidence.
- Secrets are never printed.

## v0.3: Adaptive scheduler

Goal: choose the best currently available agent for a routed task.

Commands:

```bash
lr decide "review this plan and find risks"
```

Acceptance criteria:

- Scheduler combines route fit, agent affinity, usage capacity, cooldown, and health.
- A high-usage provider is naturally deprioritized.
- A provider in cooldown is skipped unless all candidates are unavailable.
- Decisions include human-readable reasoning.

## v0.4: CLI executor bridge

Goal: optionally run the selected CLI.

Commands:

```bash
lr run "compare these docs and summarize tradeoffs"
```

Acceptance criteria:

- Execution is opt-in and visible.
- Commands are configured, not hard-coded.
- Exit codes and basic usage observations are recorded.
- Fallback is attempted only for safe/retryable failures.

## v0.5: Local OpenAI-compatible gateway

Optional later phase inspired by 9router.

Goal: provide a local endpoint for tools that speak OpenAI-compatible APIs.

Non-MVP because it adds streaming, auth, proxy, and translation complexity.

## Suggested first code scaffold

```text
pyproject.toml
src/letitbe_router/
  __init__.py
  cli.py
  config.py
  domain.py
  routes.py
  scheduler.py
  backends/
    __init__.py
    semantic_router.py
  usage/
    __init__.py
    models.py
    codex.py
    gemini.py
    claude.py
  ledger.py
tests/
  test_routes.py
  test_scheduler.py
  test_usage_models.py
  test_semantic_router_contract.py
```

## Test strategy

- Unit tests for domain models and scheduler math.
- Contract tests for the semantic-router adapter.
- Fixture-driven tests for usage collector parsing.
- No live credential tests in CI by default.
- Live probes should require explicit opt-in.
