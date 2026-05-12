<div align="center">

# letitbe-router

**Flow-safe routing for AI agents and model CLIs**<br />
**AI 에이전트와 모델 CLI를 리밋에 막히지 않게 흘려보내는 로컬 라우터**

<br />

<a href="README.ko.md"><b>한국어로 보기</b></a>
&nbsp;&nbsp;·&nbsp;&nbsp;
<a href="README.en.md"><b>Read in English</b></a>

<br /><br />

<a href="docs/architecture.md">Architecture</a>
&nbsp;·&nbsp;
<a href="docs/mvp.md">MVP</a>
&nbsp;·&nbsp;
<a href="docs/usage-model.md">Usage Model</a>
&nbsp;·&nbsp;
<a href="docs/references.md">References</a>

<br /><br />

<img alt="status: design-first" src="https://img.shields.io/badge/status-design--first-7c3aed" />
<img alt="license: MIT" src="https://img.shields.io/badge/license-MIT-111827" />
<img alt="local-first" src="https://img.shields.io/badge/local--first-yes-10b981" />

</div>

---

## Quick language select

| Language | Start here | Summary |
| --- | --- | --- |
| 한국어 | [README.ko.md](README.ko.md) | 레리삐 라우터의 비전, MVP, CLI 흐름을 한국어로 봅니다. |
| English | [README.en.md](README.en.md) | Read the project overview, architecture links, and MVP scope in English. |

## What is this?

Letitbe Router is a local-first routing layer that combines semantic intent routing with adaptive usage-aware scheduling.

It is designed to route work across Codex CLI, Gemini CLI, and Claude Code CLI while avoiding overloading any single provider or limit window.

## Reading order

1. [한국어 소개](README.ko.md) or [English overview](README.en.md)
2. [Architecture](docs/architecture.md)
3. [MVP Plan](docs/mvp.md)
4. [Usage and Limit Model](docs/usage-model.md)
5. [Reference Repository Notes](docs/references.md)

## Current status

Design-first MVP. The repository now includes the first offline v0.1 router scaffold:

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m letitbe_router.cli smoke
.venv/bin/python -m letitbe_router.cli route "fix pytest and update code"
```

The packaged CLI entrypoint is available as `lr` after editable install. For machine-wide local use, the current recommended setup is a dedicated venv plus a `~/.local/bin/lr` wrapper.

```bash
python3.12 -m venv ~/.local/share/letitbe-router-venv
~/.local/share/letitbe-router-venv/bin/python -m pip install -U git+https://github.com/misolove/letitbe-router.git
cat > ~/.local/bin/lr <<'SH'
#!/usr/bin/env sh
exec "$HOME/.local/share/letitbe-router-venv/bin/lr" "$@"
SH
chmod +x ~/.local/bin/lr
```

```bash
lr smoke
lr route "review this architecture for risks"
lr run "Reply exactly: LTR_OK" --agent claude-code --timeout 120
```

`lr run` executes the selected CLI agent in a conservative non-interactive mode:

- `codex-cli`: `codex exec --sandbox read-only --skip-git-repo-check ...`
- `gemini-cli`: `gemini --prompt ... --approval-mode plan`
- `claude-code`: `claude --print ... --permission-mode plan --max-turns 1`

Use `--dry-run` to inspect the selected command before execution.

```bash
lr run "fix pytest and update code" --dry-run
```
