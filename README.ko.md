# letitbe-router

[English](README.en.md) · [언어 선택 화면](README.md)

**Letitbe Router**는 Codex CLI, Gemini CLI, Claude Code CLI 같은 AI 에이전트/모델 CLI를 위한 **local-first 라우팅 레이어**입니다.

목표는 단순합니다.

> 작업의 성격을 이해하고, 지금 가장 덜 막힐 에이전트에게 자연스럽게 넘긴다.

즉, `semantic-router`처럼 의도를 분류하고, `9router`처럼 로컬 라우터 UX를 가져오되, `openusage`처럼 각 CLI의 사용량/리밋 신호를 읽어서 한쪽 모델에 리밋이 몰리지 않게 조절합니다.

## 한 줄 요약

```text
semantic routing + adaptive limit-aware scheduling = flow-safe AI work router
```

한국어로는:

```text
의미 기반 라우팅 + 사용량 기반 스케줄링 = 리밋에 덜 막히는 AI 작업 라우터
```

## 왜 필요한가

AI 작업을 하다 보면 이런 일이 자주 생깁니다.

- Codex는 코드 작업에 좋은데 특정 window에서 막힘
- Claude는 리뷰/설계에 좋은데 세션 리밋이 아까움
- Gemini는 리서치에 여유가 있는데 수동으로 넘기기 귀찮음
- 어떤 모델이 지금 여유 있는지 매번 사람이 판단해야 함
- 여러 CLI가 각자 다른 인증/사용량/쿨다운 방식을 가짐

Letitbe Router는 이 판단을 로컬에서 자동화하려고 합니다.

## 핵심 철학

### 1. Wrapper, not fork

`semantic-router`를 fork하지 않습니다. 대신 좁은 adapter boundary로 감싸서 upstream이 업데이트되어도 Letitbe Router 쪽에서 능동적으로 대응할 수 있게 합니다.

### 2. Observable over magical

정확히 “토큰 N개 남음”처럼 알 수 없는 것을 아는 척하지 않습니다.

대신:

- provider가 보고한 사용률
- reset time
- 최근 429/rate limit 에러
- 로컬 token/cost log
- cached usage snapshot
- confidence level

을 조합해 **adaptive signal**로 사용합니다.

### 3. Local-first

기본 상태는 로컬에 둡니다.

```text
~/.config/letitbe-router/config.yaml
~/.local/share/letitbe-router/router.db
~/.cache/letitbe-router/usage.json
```

### 4. CLI-first

처음부터 대시보드, MITM, tray app, background gateway를 만들지 않습니다.

먼저 작고 검증 가능한 CLI부터 시작합니다.

## 계획 중인 CLI

```bash
lr route "fix the failing pytest and update the code"
lr usage
lr status
lr decide "review this architecture for risks"
lr smoke
```

나중에 실행까지 붙이면:

```bash
lr run "compare these docs and summarize the tradeoffs"
```

## 어떻게 판단하나

Letitbe Router는 두 단계로 판단합니다.

### 1단계: 이 작업은 무엇인가?

예:

```text
"fix failing tests"       → code_worker
"compare documentation"   → research
"review architecture"     → review
```

이 부분은 `semantic-router` adapter가 담당합니다.

### 2단계: 지금 누구에게 보낼까?

예:

```text
code_worker 후보: codex-cli, claude-code, gemini-cli
review 후보:      claude-code, gemini-cli, codex-cli
research 후보:    gemini-cli, claude-code, codex-cli
```

여기에 usage/limit 신호를 더합니다.

```text
score = route_fit
      × agent_affinity
      × available_capacity
      × health_score
      × quality_weight
      × cost_weight
      - cooldown_penalty
      - recent_error_penalty
```

## 초기 대상 에이전트

- Codex CLI
- Gemini CLI
- Claude Code CLI

## 참고하는 프로젝트

### semantic-router

https://github.com/aurelio-labs/semantic-router

역할:

- 의도 기반 route 분류 엔진
- Letitbe Router에서는 adapter로 감싸서 사용

### 9router

https://github.com/decolua/9router

역할:

- 로컬 라우터 UX
- alias/combo/fallback 개념 참고

MVP에서는 다음은 제외합니다.

- 공격적인 process kill
- MITM
- 무거운 dashboard
- 숨은 native dependency 자동 설치

### openusage

https://github.com/robinebers/openusage

역할:

- Codex/Gemini/Claude 사용량 collector 참고
- usage window, cache, confidence 모델 참고

주의:

- 일부 usage API는 reverse-engineered이므로 정확한 quota oracle이 아니라 adaptive signal로 다룹니다.

## MVP 로드맵

### v0.1 Dry-run semantic router

```bash
lr route "fix failing tests and update the code"
lr smoke
```

실제 실행 없이 route와 후보만 결정합니다.

### v0.2 Usage collectors

```bash
lr usage
lr status
```

Codex/Gemini/Claude의 usage signal을 읽고 cache합니다.

### v0.3 Adaptive scheduler

```bash
lr decide "review this plan and find risks"
```

route 결과와 usage signal을 조합해 지금 가장 좋은 후보를 선택합니다.

### v0.4 CLI executor bridge

```bash
lr run "compare these docs and summarize tradeoffs"
```

선택된 CLI를 실제로 실행합니다. 실행은 명시적 opt-in으로만 동작합니다.

### v0.5 Local gateway

나중에 필요하면 OpenAI-compatible local endpoint를 추가합니다. 다만 streaming, auth, format translation 복잡도가 커서 MVP에서는 제외합니다.

## 문서

- [Architecture](docs/architecture.md)
- [MVP Plan](docs/mvp.md)
- [Usage and Limit Model](docs/usage-model.md)
- [Reference Repository Notes](docs/references.md)

## 현재 상태

Design-first MVP입니다. architecture, MVP 범위, usage model을 먼저 고정했고, 현재는 첫 번째 offline v0.1 라우터 스캐폴드가 들어간 상태입니다.

```bash
python3.12 -m venv .venv
.venv/bin/python -m pip install -e ".[dev]"
.venv/bin/python -m letitbe_router.cli smoke
.venv/bin/python -m letitbe_router.cli route "fix pytest and update code"
```

editable install 후에는 `lr` 명령을 목표로 합니다.

```bash
lr smoke
lr route "review this architecture for risks"
```

## 라이선스

MIT. 자세한 내용은 [LICENSE](LICENSE)를 참고하세요.

상위 참고 프로젝트들도 MIT 기반이며, 실제 코드 복사/적용이 생길 경우 notice를 유지합니다.
