# Usage and Limit Model

Letitbe Router should not pretend to know exact limits when providers expose only percentages or reset windows. The model separates observed facts from estimates.

## Core types

### UsageWindow

```python
@dataclass(frozen=True)
class UsageWindow:
    provider: str
    scope: str
    used: float
    limit: float
    unit: str
    resets_at: datetime | None
    period_ms: int | None
    model: str | None
    source: str
    confidence: str
```

Recommended fields:

- `provider`: `codex`, `gemini`, `claude`
- `scope`: `session`, `weekly`, `model`, `credits`, `local_tokens`
- `unit`: `percent`, `tokens`, `requests`, `credits`, `usd`
- `source`: `official_api`, `reverse_engineered_api`, `local_log`, `estimated`, `cache`
- `confidence`: `high`, `medium`, `low`, `unknown`

### ProviderUsageSnapshot

```python
@dataclass(frozen=True)
class ProviderUsageSnapshot:
    provider: str
    display_name: str
    plan: str | None
    windows: list[UsageWindow]
    fetched_at: datetime
    stale: bool
    error: str | None
```

### LimitSignal

A scheduler-friendly summary:

```python
@dataclass(frozen=True)
class LimitSignal:
    provider: str
    capacity_ratio: float | None
    constrained: bool
    cooldown_until: datetime | None
    reset_hint: datetime | None
    confidence: str
    reasons: list[str]
```

## Capacity calculation

If a usage window reports `used=62`, `limit=100`, `unit=percent`:

```text
capacity_ratio = 1 - used / limit = 0.38
```

If multiple windows apply, use the most constrained reliable window:

```text
capacity_ratio = min(window_capacity_ratios)
```

If all data is unknown:

```text
capacity_ratio = null
confidence = unknown
```

Schedulers should not treat unknown as zero. A reasonable MVP default is:

```text
unknown_capacity_default = 0.45
```

with a lower confidence and explanation.

## Observable vs estimated

### Observable

- Provider-reported usage percentage
- reset timestamp
- plan/tier text
- credit balance when exposed
- local token/cost logs
- recent 429 or quota errors

### Estimated

- exact remaining request count
- exact remaining token count
- relation between local token logs and subscription quota
- Gemini bucket-to-model mapping when not explicitly labeled
- quota use by other tools outside this machine

## Provider notes

### Codex CLI

Useful signals adapted from OpenUsage analysis:

- OAuth credential discovery from Codex config/keychain locations
- `wham/usage` style usage endpoint
- session and weekly usage percentages
- optional local token/cost logs through Codex usage tooling

Confidence: medium, because endpoint behavior is reverse-engineered and may change.

### Claude Code CLI

Useful signals:

- Claude Code OAuth credential discovery
- OAuth usage endpoint
- 5-hour session and weekly windows
- model-specific weekly windows where available
- local `ccusage` token/cost logs as auxiliary data

Confidence: medium unless the provider returns a complete live response.

### Gemini CLI

Useful signals:

- Gemini OAuth credential discovery
- quota bucket retrieval
- Pro/Flash remaining fractions when available

Confidence: medium to low for bucket interpretation unless the API clearly labels a model family.

## Cache policy

- Cache successful live probe results.
- Do not replace a successful cache with a failed probe.
- Mark cached results as stale when older than the configured TTL.
- Include `fetched_at` and source metadata.
- Redact tokens, emails when requested, and all secrets by default.

## Scheduler use

Usage signals should affect priority, not absolute truth.

Examples:

- 90% session usage: strong downweight.
- cooldown until future: skip candidate.
- stale medium-confidence cache: mild downweight.
- unknown usage but healthy CLI exists: allow as fallback.
