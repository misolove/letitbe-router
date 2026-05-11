# Reference Repository Notes

Letitbe Router is informed by three upstream projects. This document records what is reused conceptually and what should be avoided.

## aurelio-labs/semantic-router

Repository: https://github.com/aurelio-labs/semantic-router

Role in Letitbe Router:

> semantic intent routing backend

Useful surfaces:

- `Route`
- `SemanticRouter`
- `HybridRouter` later
- `RouteChoice`
- `RouterConfig` for reference only

Integration policy:

- Depend on `semantic-router>=0.1.12,<0.2` initially.
- Import it only from `letitbe_router.backends.semantic_router`.
- Convert Letitbe route config into upstream `Route` at runtime.
- Convert upstream `RouteChoice` into Letitbe-owned DTOs.
- Maintain adapter contract tests so upstream updates can be evaluated quickly.

Known cautions from inspection:

- Upstream package metadata and `semantic_router.__version__` can disagree.
- Docs mention a `hybrid` extra, but inspected package extras did not include that exact name.
- Some deprecated code is marked for possible removal in `v0.2.0`.
- Optional dependencies vary widely by encoder/index/provider.

License:

- MIT License
- Copyright 2024 Aurelio AI

## decolua/9router

Repository: https://github.com/decolua/9router

Role in Letitbe Router:

> UX and fallback reference for local AI routing

Useful ideas:

- one local router endpoint for many tools
- `provider/model` model naming
- aliases and combos
- account/provider fallback
- cooldown after rate limit or auth errors
- request/usage observability
- CLI setup guidance

What not to copy into the MVP:

- aggressive process killing
- MITM setup
- tray app
- heavy Next.js dashboard
- hidden native dependency self-healing
- broad automatic modification of user tool configs

License:

- MIT License
- Copyright 2024-2026 decolua and contributors

## robinebers/openusage

Repository: https://github.com/robinebers/openusage

Role in Letitbe Router:

> usage/limit signal reference for Codex, Gemini, and Claude Code

Useful ideas:

- provider plugin/collector pattern
- normalized progress lines
- credential discovery for local CLIs
- token refresh flows
- cached live probe snapshots
- stale-safe behavior
- source and confidence metadata

Target providers for the first Letitbe Router implementation:

- Codex CLI
- Gemini CLI
- Claude Code CLI

Important caution:

Many usage APIs are reverse-engineered or undocumented. Letitbe Router must present them as adaptive signals, not guaranteed quota truth.

License:

- MIT License
- Copyright 2026 Robin Ebers

## Attribution policy

If code is copied or substantially adapted from any upstream repository, preserve the upstream MIT license notice and add a notice entry.

If only ideas and architecture are referenced, keep this document as design attribution and maintain dependency license metadata.
