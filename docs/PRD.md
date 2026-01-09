# PRD: Multi-LLM Hub API

## 1. 개요 (Overview)

### 1.1 제품명

LLM MCP Hub

### 1.2 목적

여러 LLM 프로바이더(Claude, Gemini 등)를 **SDK/API 기반**으로 통합하여 **REST API 및 MCP(Model Context Protocol) 서버**로 제공하는 허브 시스템

### 1.3 배경

- 다양한 LLM 서비스를 활용해야 하는 요구사항 증가
- 각 LLM의 장점을 상황에 맞게 활용하고자 하는 니즈
- 통일된 인터페이스로 LLM 전환 비용 절감
- 기존 Claude와 Gemini를 구독하고 있지만 n8n 등 API 연계가 필요할 때 별도의 API Key를 발급 받아서 추가 비용 발생을 절감하기 위한 목적
- MCP 생태계 확장으로 AI 에이전트/도구들이 표준화된 방식으로 LLM에 접근할 필요성 증가

### 1.4 전제조건 (Constraints)

> **중요: API Key 방식 사용 금지**

- **LLM API Key를 절대 사용하지 않음** (Anthropic API Key, Google AI API Key 등)
- 이유: API Key 사용 시 사용량에 따른 별도 비용이 발생하므로, 기존 구독 플랜의 비용 절감 목적에 위배됨
- **Claude**: `claude-agent-sdk` + OAuth 토큰으로 기존 구독(Claude Pro/Max) 활용
- **Gemini**: `ptyprocess` + Gemini CLI로 기존 구독(Gemini Advanced) 활용
- Docker 컨테이너 환경에서 OAuth 토큰을 환경변수/파일로 관리

| 인증 방식 | 사용 여부 | 비고 |
|-----------|----------|------|
| Anthropic API Key | **금지** | 사용량 기반 과금 |
| Google AI API Key | **금지** | 사용량 기반 과금 |
| Claude Agent SDK + OAuth | **사용** | 구독 플랜 활용, TTY 불필요 |
| Gemini CLI + PTY Wrapper | **사용** | 구독 플랜 활용 |
| `CLAUDE_CODE_OAUTH_TOKEN` 환경변수 | **사용** | SDK 인증용 |

---

## 2. 목표 (Goals)

### 2.1 핵심 목표

- [ ] 멀티 LLM 통합 API 제공
- [ ] MCP 서버로 AI 에이전트/도구 연동 지원
- [ ] Claude Agent SDK 기반 안정적인 Claude 연동
- [ ] Gemini PTY Wrapper 기반 Gemini 연동
- [ ] 확장 가능한 아키텍처 설계

### 2.2 성공 지표

| 지표              | 목표값                        |
| ----------------- | ----------------------------- |
| API 응답 시간     | < 100ms (LLM 응답 제외)       |
| 가용성            | 99.9%                         |
| 지원 LLM 수       | 2개 이상 (Claude, Gemini)     |
| MCP 클라이언트    | Claude Desktop, Cursor 연동   |
| 세션 유지         | 1시간 TTL, 대화 컨텍스트 유지 |
| 토큰 갱신 알림    | 만료 3일 전 자동 알림         |

---

## 3. 사용자 및 시나리오 (Users & Use Cases)

### 3.1 대상 사용자

- **개발자**: API를 통해 멀티 LLM 활용
- **시스템 관리자**: LLM 프로세스 모니터링 및 관리

### 3.2 주요 사용 시나리오

1. **LLM 선택 요청**: 특정 LLM을 지정하여 프롬프트 전송
2. **자동 라우팅**: 요청 특성에 따라 최적 LLM 자동 선택
3. **Fallback 처리**: 특정 LLM 장애 시 다른 LLM으로 자동 전환
4. **MCP 클라이언트 연동**: Claude Desktop, Cursor 등 MCP 클라이언트에서 허브를 통해 멀티 LLM 활용
5. **n8n/자동화 도구 연동**: REST API 또는 MCP를 통해 워크플로우 자동화

---

## 4. 기능 요구사항 (Functional Requirements)

### 4.1 Core Features

#### F1: LLM Provider 관리

| ID   | 기능                             | 우선순위 | 상태   |
| ---- | -------------------------------- | -------- | ------ |
| F1.1 | Claude Agent SDK 연동            | P0       | 미착수 |
| F1.2 | Gemini PTY Wrapper 연동          | P0       | 미착수 |
| F1.3 | Provider 상태 모니터링           | P1       | 미착수 |
| F1.4 | 동적 Provider 추가/제거          | P2       | 미착수 |

#### F2: API Gateway

| ID   | 기능                     | 우선순위 | 상태   |
| ---- | ------------------------ | -------- | ------ |
| F2.1 | REST API 엔드포인트 제공 | P0       | 미착수 |
| F2.2 | 요청 라우팅              | P0       | 미착수 |
| F2.3 | 스트리밍 응답 지원       | P1       | 미착수 |
| F2.4 | 인증/인가                | P1       | 미착수 |

#### F3: OAuth 토큰 관리

| ID   | 기능                                    | 우선순위 | 상태   |
| ---- | --------------------------------------- | -------- | ------ |
| F3.1 | Claude OAuth 토큰 환경변수 관리         | P0       | 미착수 |
| F3.2 | Gemini OAuth 토큰 파일 마운트 관리      | P0       | 미착수 |
| F3.3 | 토큰 만료 감지 및 헬스체크              | P1       | 미착수 |
| F3.4 | 토큰 만료 알림 (Slack/Email)            | P1       | 미착수 |

#### F4: 세션 관리

| ID   | 기능                                         | 우선순위 | 상태   |
| ---- | -------------------------------------------- | -------- | ------ |
| F4.1 | HTTP 헤더 기반 세션 ID 전달 (`X-Session-ID`) | P0       | 미착수 |
| F4.2 | Redis 기반 세션 저장소                       | P0       | 미착수 |
| F4.3 | 대화 기록 (messages) 세션 저장               | P0       | 미착수 |
| F4.4 | 세션 만료 관리 (TTL: 1시간)                  | P1       | 미착수 |
| F4.5 | 세션 조회/삭제 API                           | P2       | 미착수 |

#### F5: MCP Server

| ID   | 기능                                    | 우선순위 | 상태   |
| ---- | --------------------------------------- | -------- | ------ |
| F5.1 | MCP 서버 구현 (stdio/SSE 전송)          | P0       | 미착수 |
| F5.2 | `chat` Tool 제공 (LLM 대화 요청)        | P0       | 미착수 |
| F5.3 | `list_providers` Tool 제공              | P1       | 미착수 |
| F5.4 | `get_session` Tool 제공 (세션 조회)     | P1       | 미착수 |
| F5.5 | Resource 제공 (Provider 정보, 세션)     | P2       | 미착수 |
| F5.6 | Prompt 템플릿 제공                      | P2       | 미착수 |

---

## 5. 비기능 요구사항 (Non-Functional Requirements)

### 5.1 성능

- 동시 요청 처리: 최소 100 concurrent requests
- 메모리 사용량: 컨테이너당 최대 2GB

### 5.2 보안

- API Key 기반 인증 (허브 자체 API Key)
- Rate Limiting
- 입력 유효성 검사
- OAuth 토큰 암호화 저장

### 5.3 운영

- 구조화된 로깅 (JSON format)
- 헬스체크 엔드포인트 (`/health`, `/health/tokens`)
- 메트릭 수집 (Prometheus 호환)
- 토큰 만료 알림 자동화

---

## 6. 기술 스택 (Tech Stack)

### 6.1 제안 스택

| 영역            | 기술                  | 선택 이유                                |
| --------------- | --------------------- | ---------------------------------------- |
| Language        | Python 3.11+          | asyncio, 타입 힌트 지원                  |
| Package Manager | uv                    | 빠른 의존성 설치, lockfile 지원          |
| Framework       | FastAPI               | 비동기, OpenAPI 자동 생성                |
| **Claude**      | **claude-agent-sdk**  | 공식 SDK, OAuth 지원, TTY 불필요         |
| **Gemini**      | **ptyprocess + CLI**  | PTY 래퍼로 CLI 제어, OAuth 토큰 사용     |
| MCP Server      | mcp (Python SDK)      | 공식 MCP Python SDK, stdio/SSE 지원      |
| Config          | Pydantic Settings     | 타입 안전한 설정 관리                    |
| Session Store   | Redis                 | 분산 환경 지원, TTL 기반 만료            |

### 6.2 주요 의존성

```toml
[project]
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "claude-agent-sdk>=0.1.0",
    "ptyprocess>=0.7.0",
    "mcp>=1.0.0",
    "redis>=5.0.0",
    "pydantic-settings>=2.0.0",
]
```

### 6.3 외부 시스템

- Claude API (claude.ai) - OAuth 토큰 인증
- Gemini API (Google) - OAuth 토큰 인증
- Redis (세션 저장소)

---

## 7. 시스템 아키텍처 (Architecture)

```
                    ┌─────────────────────────────────────┐
                    │            Clients                  │
                    ├─────────────────┬───────────────────┤
                    │  REST API       │  MCP Clients      │
                    │  (n8n, curl)    │  (Claude Desktop, │
                    │                 │   Cursor, etc.)   │
                    └────────┬────────┴─────────┬─────────┘
                             │                  │
                             ▼                  ▼
┌────────────────────────────────────────────────────────────────┐
│                        LLM MCP Hub                             │
├────────────────────────────┬───────────────────────────────────┤
│      REST API Layer        │         MCP Server Layer          │
│      (FastAPI)             │         (mcp SDK)                 │
│  ┌──────────────────────┐  │  ┌─────────────────────────────┐  │
│  │ POST /v1/chat/...    │  │  │ Tools:                      │  │
│  │ GET  /v1/sessions/.. │  │  │  - chat                     │  │
│  │ GET  /v1/providers   │  │  │  - list_providers           │  │
│  │ GET  /health         │  │  │  - get_session              │  │
│  │ GET  /health/tokens  │  │  │ Resources:                  │  │
│  └──────────────────────┘  │  │  - provider://              │  │
│                            │  │  - session://               │  │
│                            │  └─────────────────────────────┘  │
├────────────────────────────┴───────────────────────────────────┤
│                      Service Layer                             │
│              (ChatService, SessionService)                     │
├────────────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                         │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │ Claude Adapter   │  │ Gemini Adapter   │  │ Session Store│  │
│  │ (Agent SDK)      │  │ (PTY + CLI)      │  │ (Redis)      │  │
│  │                  │  │                  │  │              │  │
│  │ CLAUDE_CODE_     │  │ ~/.gemini/       │  │ TTL: 1 hour  │  │
│  │ OAUTH_TOKEN      │  │ oauth_creds.json │  │              │  │
│  └────────┬─────────┘  └────────┬─────────┘  └──────────────┘  │
└───────────┼─────────────────────┼──────────────────────────────┘
            │                     │
            ▼                     ▼
  ┌─────────────────┐   ┌─────────────────┐
  │  Claude API     │   │  Gemini API     │
  │  (claude.ai)    │   │  (Google)       │
  │  Pro/Max 구독   │   │  Advanced 구독  │
  └─────────────────┘   └─────────────────┘
```

---

## 8. Provider 구현 상세

### 8.1 Claude Provider (Agent SDK)

**장점:**
- 공식 SDK로 안정적
- TTY 불필요 (컨테이너 친화적)
- OAuth 토큰 환경변수로 간편 설정
- AsyncIterator로 스트리밍 지원

**환경변수:**
```bash
CLAUDE_CODE_OAUTH_TOKEN=your-oauth-token-here
CLAUDE_MODEL=claude-sonnet-4-5-20250929
```

**구현 예시:**
```python
import anyio
from claude_agent_sdk import query, ClaudeSDKClient

class ClaudeAdapter:
    async def chat(self, prompt: str) -> str:
        result = []
        async for message in query(prompt=prompt):
            result.append(str(message))
        return "".join(result)

    async def chat_stream(self, prompt: str):
        async for message in query(prompt=prompt):
            yield message

    async def chat_with_session(self, prompt: str):
        async with ClaudeSDKClient() as client:
            response = await client.send(prompt)
            return response
```

### 8.2 Gemini Provider (PTY Wrapper)

**배경:**
- Gemini CLI는 TTY가 필요함
- 컨테이너 환경에서 TTY가 없어 직접 subprocess 호출 불가
- `ptyprocess` 라이브러리로 가상 TTY 생성하여 해결

**환경변수:**
```bash
GEMINI_AUTH_PATH=/mnt/auth/gemini/oauth_creds.json
GEMINI_MODEL=gemini-2.5-pro
```

**구현 예시:**
```python
from ptyprocess import PtyProcess
import os

class GeminiAdapter:
    def __init__(self, auth_path: str):
        self.auth_path = auth_path
        # OAuth 토큰 파일을 ~/.gemini/에 심볼릭 링크
        self._setup_auth()

    def _setup_auth(self):
        gemini_dir = os.path.expanduser("~/.gemini")
        os.makedirs(gemini_dir, exist_ok=True)
        # 토큰 파일 링크 또는 복사

    async def chat(self, prompt: str) -> str:
        proc = PtyProcess.spawn(
            ["gemini", "-p", prompt],
            env={**os.environ, "HOME": os.path.expanduser("~")}
        )

        output = ""
        while proc.isalive():
            try:
                output += proc.read(1024).decode()
            except EOFError:
                break

        proc.close()
        return self._parse_output(output)

    def _parse_output(self, raw: str) -> str:
        # ANSI escape 코드 제거 및 응답 파싱
        import re
        clean = re.sub(r'\x1b\[[0-9;]*m', '', raw)
        return clean.strip()
```

---

## 9. API 명세 (API Specification)

### 9.1 세션 관리 헤더

| 헤더           | 방향     | 설명                          |
| -------------- | -------- | ----------------------------- |
| `X-Session-ID` | Request  | 세션 ID (없으면 새 세션 생성) |
| `X-Session-ID` | Response | 생성/사용된 세션 ID 반환      |

### 9.2 엔드포인트

#### POST /v1/chat/completions

통합 채팅 완성 요청

**Request Headers:**

```
X-Session-ID: abc123-def456-... (optional)
```

**Request Body:**

```json
{
  "provider": "claude" | "gemini" | "auto",
  "model": "string",
  "messages": [
    {"role": "user", "content": "string"}
  ],
  "stream": false,
  "max_tokens": 1024
}
```

**Response Headers:**

```
X-Session-ID: abc123-def456-...
```

**Response Body:**

```json
{
  "id": "string",
  "provider": "claude",
  "model": "claude-sonnet-4-5-20250929",
  "choices": [
    {
      "message": {
        "role": "assistant",
        "content": "string"
      }
    }
  ],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 20
  }
}
```

#### GET /v1/sessions/{session_id}

세션 정보 조회

**Response:**

```json
{
  "session_id": "string",
  "messages": [
    { "role": "user", "content": "string" },
    { "role": "assistant", "content": "string" }
  ],
  "created_at": "2026-01-05T12:00:00Z",
  "updated_at": "2026-01-05T12:30:00Z"
}
```

#### DELETE /v1/sessions/{session_id}

세션 삭제

**Response:**
```json
{
  "success": true,
  "message": "Session deleted"
}
```

#### GET /v1/providers

사용 가능한 Provider 목록

**Response:**
```json
{
  "providers": [
    {
      "name": "claude",
      "status": "available",
      "models": ["claude-sonnet-4-5-20250929", "claude-opus-4-5-20250929"],
      "auth_method": "oauth_token"
    },
    {
      "name": "gemini",
      "status": "available",
      "models": ["gemini-2.5-pro", "gemini-2.5-flash"],
      "auth_method": "oauth_file"
    }
  ]
}
```

#### GET /health

헬스체크

**Response:**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "providers": {
    "claude": "up",
    "gemini": "up"
  },
  "redis": "connected"
}
```

#### GET /health/tokens

OAuth 토큰 상태 확인

**Response:**
```json
{
  "claude": {
    "status": "valid",
    "expires_at": "2026-01-15T12:00:00Z",
    "days_remaining": 7
  },
  "gemini": {
    "status": "warning",
    "expires_at": "2026-01-12T12:00:00Z",
    "days_remaining": 3,
    "message": "Token expires soon, please refresh"
  }
}
```

---

## 10. MCP 명세 (MCP Specification)

### 10.1 서버 정보

```json
{
  "name": "llm-mcp-hub",
  "version": "0.1.0",
  "description": "Multi-LLM Hub - Access Claude, Gemini via unified interface"
}
```

### 10.2 Tools

#### chat
LLM에 대화 요청

```json
{
  "name": "chat",
  "description": "Send a message to LLM and get a response",
  "inputSchema": {
    "type": "object",
    "properties": {
      "provider": {
        "type": "string",
        "enum": ["claude", "gemini", "auto"],
        "description": "LLM provider to use"
      },
      "message": {
        "type": "string",
        "description": "User message"
      },
      "session_id": {
        "type": "string",
        "description": "Session ID for conversation context (optional)"
      },
      "model": {
        "type": "string",
        "description": "Specific model to use (optional)"
      }
    },
    "required": ["message"]
  }
}
```

#### list_providers
사용 가능한 Provider 목록 조회

```json
{
  "name": "list_providers",
  "description": "List available LLM providers and their status",
  "inputSchema": {
    "type": "object",
    "properties": {}
  }
}
```

#### get_session
세션 정보 조회

```json
{
  "name": "get_session",
  "description": "Get session information including message history",
  "inputSchema": {
    "type": "object",
    "properties": {
      "session_id": {
        "type": "string",
        "description": "Session ID to retrieve"
      }
    },
    "required": ["session_id"]
  }
}
```

### 10.3 Resources

| URI 패턴                     | 설명                    |
| ---------------------------- | ----------------------- |
| `provider://list`            | Provider 목록           |
| `provider://{name}`          | 특정 Provider 상세 정보 |
| `session://{session_id}`     | 세션 정보 및 대화 기록  |

### 10.4 Prompts

| 이름              | 설명                              |
| ----------------- | --------------------------------- |
| `summarize`       | 대화 내용 요약 요청               |
| `translate`       | 번역 요청 (언어 지정)             |
| `code_review`     | 코드 리뷰 요청                    |

### 10.5 전송 방식

| 방식  | 용도                                      |
| ----- | ----------------------------------------- |
| stdio | Claude Desktop, 로컬 CLI 연동             |
| SSE   | 웹 기반 클라이언트, 원격 연동             |

### 10.6 클라이언트 설정 예시

**Claude Desktop (`claude_desktop_config.json`)**:
```json
{
  "mcpServers": {
    "llm-hub": {
      "command": "uv",
      "args": ["run", "llm-mcp-hub-server"],
      "env": {
        "REDIS_URL": "redis://localhost:6379",
        "CLAUDE_CODE_OAUTH_TOKEN": "${CLAUDE_CODE_OAUTH_TOKEN}"
      }
    }
  }
}
```

---

## 11. 프로젝트 구조 (Project Structure)

```
llm-mcp-hub/
├── docs/
│   ├── PRD.md
│   ├── 토큰생성방법.md
│   └── azure-cloud-container.md
├── src/
│   └── llm_mcp_hub/
│       ├── __init__.py
│       ├── main.py                  # FastAPI 앱 진입점
│       │
│       ├── core/                    # 핵심 설정 및 공통 모듈
│       │   ├── __init__.py
│       │   ├── config.py            # Pydantic Settings
│       │   ├── exceptions.py        # 커스텀 예외 정의
│       │   └── dependencies.py      # 공통 의존성 (Redis 등)
│       │
│       ├── domain/                  # 도메인 모델 (비즈니스 로직)
│       │   ├── __init__.py
│       │   ├── message.py           # Message 도메인 모델
│       │   └── session.py           # Session 도메인 모델
│       │
│       ├── infrastructure/          # 외부 시스템 연동
│       │   ├── __init__.py
│       │   ├── session/             # 세션 저장소
│       │   │   ├── __init__.py
│       │   │   ├── base.py          # 추상 저장소 인터페이스
│       │   │   ├── redis.py         # Redis 구현체
│       │   │   └── memory.py        # 인메모리 구현체 (테스트용)
│       │   └── providers/           # LLM Provider Adapters
│       │       ├── __init__.py
│       │       ├── base.py          # Provider 추상 클래스
│       │       ├── claude.py        # Claude Agent SDK Adapter
│       │       └── gemini.py        # Gemini PTY Adapter
│       │
│       ├── api/                     # REST API 계층 (Presentation)
│       │   ├── __init__.py
│       │   ├── v1/                  # API 버전 관리
│       │   │   ├── __init__.py
│       │   │   ├── router.py        # v1 라우터 통합
│       │   │   ├── chat.py          # /chat/completions
│       │   │   ├── sessions.py      # /sessions
│       │   │   └── providers.py     # /providers
│       │   ├── schemas/             # API 스키마 (Request/Response)
│       │   │   ├── __init__.py
│       │   │   ├── chat.py
│       │   │   ├── session.py
│       │   │   └── common.py
│       │   └── middleware/          # 미들웨어
│       │       ├── __init__.py
│       │       └── session.py       # 세션 미들웨어
│       │
│       ├── mcp/                     # MCP Server 계층
│       │   ├── __init__.py
│       │   ├── server.py            # MCP 서버 메인
│       │   ├── tools/               # MCP Tools
│       │   │   ├── __init__.py
│       │   │   ├── chat.py          # chat tool
│       │   │   ├── providers.py     # list_providers tool
│       │   │   └── sessions.py      # get_session tool
│       │   ├── resources/           # MCP Resources
│       │   │   ├── __init__.py
│       │   │   ├── provider.py      # provider:// 리소스
│       │   │   └── session.py       # session:// 리소스
│       │   └── prompts/             # MCP Prompts
│       │       ├── __init__.py
│       │       └── templates.py     # 프롬프트 템플릿
│       │
│       └── services/                # 비즈니스 서비스 계층
│           ├── __init__.py
│           ├── chat.py              # 채팅 서비스
│           └── session.py           # 세션 서비스
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py                  # pytest fixtures
│   ├── unit/
│   └── integration/
│
├── pyproject.toml
├── uv.lock
├── .env.example
├── .gitignore
├── CLAUDE.md
├── GEMINI.md
└── README.md
```

### 11.1 구조 설계 원칙

1. **계층 분리**: API(Presentation) → Services(Application) → Domain → Infrastructure
2. **의존성 역전**: Infrastructure는 인터페이스에 의존 (저장소/Provider 교체 용이)
3. **API 버전 관리**: `/api/v1/`, `/api/v2/` 형태로 확장 가능
4. **모듈화**: 새로운 Provider 추가 시 `infrastructure/providers/`에 파일만 추가
5. **테스트 용이성**: 인메모리 구현체로 외부 의존성 없이 테스트 가능

---

## 12. 마일스톤 (Milestones)

### Phase 1: Foundation

- [ ] 프로젝트 초기 설정 (uv, pyproject.toml)
- [ ] 기본 FastAPI 서버 구축
- [ ] Redis 세션 저장소 구현
- [ ] Claude Agent SDK 연동 (OAuth 토큰)
- [ ] 기본 `/v1/chat/completions` API

### Phase 2: Provider Integration

- [ ] Gemini PTY Adapter 구현
- [ ] Provider 라우팅 로직
- [ ] `/v1/providers` API
- [ ] `/health/tokens` API

### Phase 3: MCP Server

- [ ] MCP 서버 기본 구조 구현
- [ ] chat Tool 구현
- [ ] list_providers, get_session Tool 구현
- [ ] Resources 구현 (provider://, session://)
- [ ] stdio/SSE 전송 지원

### Phase 4: Production Ready

- [ ] 에러 핸들링 및 fallback
- [ ] 로깅 및 모니터링
- [ ] 토큰 만료 알림 자동화
- [ ] 테스트 및 문서화
- [ ] Docker 이미지 최적화

---

## 13. 리스크 및 고려사항 (Risks & Considerations)

| 리스크                    | 영향도 | 대응 방안                                    |
| ------------------------- | ------ | -------------------------------------------- |
| OAuth 토큰 만료           | 높음   | 헬스체크 API, 만료 알림, 1~2주 갱신 주기     |
| Gemini PTY 불안정         | 중간   | 재시도 로직, 타임아웃 설정, 에러 파싱        |
| API Rate Limit            | 높음   | Provider별 rate limiting, 큐잉               |
| Redis 연결 장애           | 높음   | 연결 풀링, 재연결 로직, 헬스체크             |
| MCP 프로토콜 버전 변경    | 중간   | SDK 버전 고정, 호환성 테스트                 |
| 세션 데이터 유실          | 중간   | Redis 영속성 설정, 백업 전략                 |
| Claude SDK 버그           | 중간   | SDK 버전 고정, 이슈 모니터링                 |

---

## 14. 참고 자료 (References)

- [Claude Agent SDK - PyPI](https://pypi.org/project/claude-agent-sdk/)
- [Claude Agent SDK - GitHub](https://github.com/anthropics/claude-agent-sdk-python)
- [Claude Agent SDK - Docs](https://platform.claude.com/docs/en/agent-sdk/python)
- [Gemini CLI - npm](https://www.npmjs.com/package/@google/gemini-cli)
- [Gemini CLI - GitHub](https://github.com/google-gemini/gemini-cli)
- [ptyprocess - PyPI](https://pypi.org/project/ptyprocess/)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

---

## 15. 변경 이력 (Changelog)

| 버전 | 날짜       | 작성자 | 변경 내용                                                                             |
| ---- | ---------- | ------ | ------------------------------------------------------------------------------------- |
| 0.1  | 2026-01-05 | -      | 초안 작성                                                                             |
| 0.2  | 2026-01-05 | -      | 세션 관리 기능 추가 (F4), 기술 스택에 uv/Redis 추가, 확장성 고려한 프로젝트 구조 변경 |
| 0.3  | 2026-01-05 | -      | MCP Server 지원 추가 (F5), MCP 명세 섹션 추가, 아키텍처 및 프로젝트 구조에 MCP 레이어 반영 |
| 0.4  | 2026-01-05 | -      | 문서 검토: 성공 지표/리스크에 MCP/Redis 항목 추가, API 명세 보완, workers 모듈 추가 |
| 0.5  | 2026-01-09 | -      | **아키텍처 변경**: subprocess → SDK 기반으로 전환. Claude Agent SDK + Gemini PTY Wrapper 도입. OAuth 토큰 관리 방식 상세화. TTY 문제 해결 방안 반영. |
