# letitbe-router

[한국어](README.ko.md) · [Language landing](README.md)

**Letitbe Router** is a local-first routing layer for AI agents and model CLIs.

It combines:

- **semantic intent routing** from [`aurelio-labs/semantic-router`](https://github.com/aurelio-labs/semantic-router)
- **simple local router UX and fallback patterns** inspired by [`decolua/9router`](https://github.com/decolua/9router)
- **adaptive usage/limit signals** inspired by [`robinebers/openusage`](https://github.com/robinebers/openusage)

The goal is to keep work flowing across Codex CLI, Gemini CLI, and Claude Code CLI without exhausting any single model, provider, or account window.

> Status: design-first MVP. The repository currently defines architecture and implementation scope before code is added.

## Why

AI coding/research/review workflows often hit uneven limits:

- one model gets exhausted while others remain available
- provider quotas reset on different windows
- CLIs expose different credential and usage surfaces
- semantic routing and limit-aware scheduling are usually handled separately

Letitbe Router treats routing as two related decisions:

1. **What kind of work is this?**
2. **Which available agent should take it right now?**

## Planned CLI

```bash
lr route "fix the failing pytest and update the code"
lr usage
lr status
lr decide "review this architecture for risks"
lr smoke
```

Future executor mode:

```bash
lr run "compare these docs and summarize the tradeoffs"
```

## Design principles

- **Wrapper, not fork:** use `semantic-router` through a narrow adapter boundary.
- **Stable domain model:** expose Letitbe Router DTOs, not upstream internals.
- **Observable over magical:** usage limits are measured or estimated with confidence labels.
- **Local-first:** default state lives under the user home directory.
- **CLI-first:** no heavy dashboard, MITM, or process-killing behavior in the MVP.
- **Safe fallback:** cooldown and fallback should degrade gracefully when a provider is unavailable.

## Reference docs

- [Architecture](docs/architecture.md)
- [MVP Plan](docs/mvp.md)
- [Usage and Limit Model](docs/usage-model.md)
- [Reference Repository Notes](docs/references.md)

## Initial target agents

- Codex CLI
- Gemini CLI
- Claude Code CLI

## License

MIT. See [LICENSE](LICENSE).

This project depends on or learns from MIT-licensed upstream projects. See [docs/references.md](docs/references.md) for attribution notes.
