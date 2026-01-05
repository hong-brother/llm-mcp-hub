# PRD: Multi-LLM Hub API

## 1. 개요 (Overview)

### 1.1 제품명

LLM MCP Hub

### 1.2 목적

여러 LLM 프로바이더(Claude, Gemini 등)를 subprocess 기반으로 통합하여 **REST API 및 MCP(Model Context Protocol) 서버**로 제공하는 허브 시스템

### 1.3 배경

- 다양한 LLM 서비스를 활용해야 하는 요구사항 증가
- 각 LLM의 장점을 상황에 맞게 활용하고자 하는 니즈
- 통일된 인터페이스로 LLM 전환 비용 절감
- 기존 claude와 gemini를 구독하고 있지만 n8n등 API연계가 필요할때 별도의 API Key를 발급 받아서 추가 비용 발생을 절감 하기 위한 목적
- MCP 생태계 확장으로 AI 에이전트/도구들이 표준화된 방식으로 LLM에 접근할 필요성 증가

---

## 2. 목표 (Goals)

### 2.1 핵심 목표

- [ ] 멀티 LLM 통합 API 제공
- [ ] MCP 서버로 AI 에이전트/도구 연동 지원
- [ ] subprocess 기반 안정적인 프로세스 관리
- [ ] 확장 가능한 아키텍처 설계

### 2.2 성공 지표

| 지표              | 목표값                        |
| ----------------- | ----------------------------- |
| API 응답 시간     | < 100ms (LLM 응답 제외)       |
| 가용성            | 99.9%                         |
| 지원 LLM 수       | 2개 이상 (Claude, Gemini)     |
| MCP 클라이언트    | Claude Desktop, Cursor 연동   |
| 세션 유지         | 1시간 TTL, 대화 컨텍스트 유지 |

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

| ID   | 기능                        | 우선순위 | 상태   |
| ---- | --------------------------- | -------- | ------ |
| F1.1 | Claude subprocess 실행/관리 | P0       | 미착수 |
| F1.2 | Gemini subprocess 실행/관리 | P0       | 미착수 |
| F1.3 | Provider 상태 모니터링      | P1       | 미착수 |
| F1.4 | 동적 Provider 추가/제거     | P2       | 미착수 |

#### F2: API Gateway

| ID   | 기능                     | 우선순위 | 상태   |
| ---- | ------------------------ | -------- | ------ |
| F2.1 | REST API 엔드포인트 제공 | P0       | 미착수 |
| F2.2 | 요청 라우팅              | P0       | 미착수 |
| F2.3 | 스트리밍 응답 지원       | P1       | 미착수 |
| F2.4 | 인증/인가                | P1       | 미착수 |

#### F3: 프로세스 관리

| ID   | 기능                         | 우선순위 | 상태   |
| ---- | ---------------------------- | -------- | ------ |
| F3.1 | subprocess 생명주기 관리     | P0       | 미착수 |
| F3.2 | 프로세스 풀 관리             | P1       | 미착수 |
| F3.3 | 자동 재시작 (crash recovery) | P1       | 미착수 |
| F3.4 | 리소스 제한 (CPU, Memory)    | P2       | 미착수 |

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
- 메모리 사용량: subprocess당 최대 512MB

### 5.2 보안

- API Key 기반 인증
- Rate Limiting
- 입력 유효성 검사

### 5.3 운영

- 구조화된 로깅 (JSON format)
- 헬스체크 엔드포인트
- 메트릭 수집 (Prometheus 호환)

---

## 6. 기술 스택 (Tech Stack)

### 6.1 제안 스택

| 영역            | 기술               | 선택 이유                            |
| --------------- | ------------------ | ------------------------------------ |
| Language        | Python 3.11+       | asyncio, subprocess 지원             |
| Package Manager | uv                 | 빠른 의존성 설치, lockfile 지원      |
| Framework       | FastAPI            | 비동기, OpenAPI 자동 생성            |
| MCP Server      | mcp (Python SDK)   | 공식 MCP Python SDK, stdio/SSE 지원  |
| Process Mgmt    | asyncio.subprocess | 네이티브 비동기 subprocess           |
| Config          | Pydantic Settings  | 타입 안전한 설정 관리                |
| Session Store   | Redis              | 분산 환경 지원, TTL 기반 만료        |

### 6.2 외부 의존성

- Claude API (Anthropic)
- Gemini API (Google)
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
│  └──────────────────────┘  │  │ Resources:                  │  │
│                            │  │  - provider://              │  │
│                            │  │  - session://               │  │
│                            │  └─────────────────────────────┘  │
├────────────────────────────┴───────────────────────────────────┤
│                      Service Layer                             │
│              (ChatService, SessionService)                     │
├────────────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Session Store│  │  Provider    │  │   Worker Manager     │  │
│  │ (Redis)      │  │  Registry    │  │   (subprocess pool)  │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
└─────────────────────────────┬──────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
    ┌─────────────────┐             ┌─────────────────┐
    │  Claude Worker  │             │  Gemini Worker  │
    │  (subprocess)   │             │  (subprocess)   │
    └────────┬────────┘             └────────┬────────┘
             │                               │
             ▼                               ▼
    ┌─────────────────┐             ┌─────────────────┐
    │  Claude API     │             │  Gemini API     │
    │  (Anthropic)    │             │  (Google)       │
    └─────────────────┘             └─────────────────┘
```

---

## 8. API 명세 (API Specification)

### 8.1 세션 관리 헤더

| 헤더           | 방향     | 설명                          |
| -------------- | -------- | ----------------------------- |
| `X-Session-ID` | Request  | 세션 ID (없으면 새 세션 생성) |
| `X-Session-ID` | Response | 생성/사용된 세션 ID 반환      |

### 8.2 엔드포인트

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
  "model": "claude-3-5-sonnet",
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
      "models": ["claude-3-5-sonnet", "claude-3-opus"]
    },
    {
      "name": "gemini",
      "status": "available",
      "models": ["gemini-pro", "gemini-ultra"]
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

---

## 9. MCP 명세 (MCP Specification)

### 9.1 서버 정보

```json
{
  "name": "llm-mcp-hub",
  "version": "0.1.0",
  "description": "Multi-LLM Hub - Access Claude, Gemini via unified interface"
}
```

### 9.2 Tools

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

### 9.3 Resources

| URI 패턴                     | 설명                    |
| ---------------------------- | ----------------------- |
| `provider://list`            | Provider 목록           |
| `provider://{name}`          | 특정 Provider 상세 정보 |
| `session://{session_id}`     | 세션 정보 및 대화 기록  |

### 9.4 Prompts

| 이름              | 설명                              |
| ----------------- | --------------------------------- |
| `summarize`       | 대화 내용 요약 요청               |
| `translate`       | 번역 요청 (언어 지정)             |
| `code_review`     | 코드 리뷰 요청                    |

### 9.5 전송 방식

| 방식  | 용도                                      |
| ----- | ----------------------------------------- |
| stdio | Claude Desktop, 로컬 CLI 연동             |
| SSE   | 웹 기반 클라이언트, 원격 연동             |

### 9.6 클라이언트 설정 예시

**Claude Desktop (`claude_desktop_config.json`)**:
```json
{
  "mcpServers": {
    "llm-hub": {
      "command": "uv",
      "args": ["run", "llm-mcp-hub-server"],
      "env": {
        "REDIS_URL": "redis://localhost:6379"
      }
    }
  }
}
```

---

## 10. 프로젝트 구조 (Project Structure)

```
llm-mcp-hub/
├── docs/
│   └── PRD.md
├── src/
│   └── llm_mcp_hub/                 # 패키지 루트
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
│       │   ├── providers/           # LLM Provider 연동
│       │   │   ├── __init__.py
│       │   │   ├── base.py          # Provider 추상 클래스
│       │   │   ├── claude.py        # Claude 구현체
│       │   │   └── gemini.py        # Gemini 구현체
│       │   └── workers/             # subprocess 관리
│       │       ├── __init__.py
│       │       ├── manager.py       # Worker 생명주기 관리
│       │       └── pool.py          # Worker 풀 관리
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
└── README.md
```

### 10.1 구조 설계 원칙

1. **계층 분리**: API(Presentation) → Services(Application) → Domain → Infrastructure
2. **의존성 역전**: Infrastructure는 인터페이스에 의존 (저장소 교체 용이)
3. **API 버전 관리**: `/api/v1/`, `/api/v2/` 형태로 확장 가능
4. **모듈화**: 새로운 Provider 추가 시 `infrastructure/providers/`에 파일만 추가
5. **테스트 용이성**: 인메모리 구현체로 외부 의존성 없이 테스트 가능

---

## 11. 마일스톤 (Milestones)

### Phase 1: Foundation

- [ ] 프로젝트 초기 설정 (uv)
- [ ] 기본 FastAPI 서버 구축
- [ ] Redis 세션 저장소 구현
- [ ] subprocess 관리 모듈 구현

### Phase 2: Provider Integration

- [ ] Claude Provider 구현
- [ ] Gemini Provider 구현
- [ ] 통합 REST API 엔드포인트

### Phase 3: MCP Server

- [ ] MCP 서버 기본 구조 구현
- [ ] chat Tool 구현
- [ ] list_providers, get_session Tool 구현
- [ ] Resources 구현 (provider://, session://)
- [ ] stdio/SSE 전송 지원

### Phase 4: Production Ready

- [ ] 에러 핸들링 및 fallback
- [ ] 로깅 및 모니터링
- [ ] 테스트 및 문서화

---

## 12. 리스크 및 고려사항 (Risks & Considerations)

| 리스크                 | 영향도 | 대응 방안                            |
| ---------------------- | ------ | ------------------------------------ |
| API Rate Limit         | 높음   | Provider별 rate limiting, 큐잉       |
| subprocess 메모리 누수 | 중간   | 주기적 재시작, 모니터링              |
| API 응답 지연          | 중간   | 타임아웃 설정, 스트리밍              |
| Redis 연결 장애        | 높음   | 연결 풀링, 재연결 로직, 헬스체크     |
| MCP 프로토콜 버전 변경 | 중간   | SDK 버전 고정, 호환성 테스트         |
| 세션 데이터 유실       | 중간   | Redis 영속성 설정, 백업 전략         |

---

## 13. 참고 자료 (References)

- [Anthropic Claude API](https://docs.anthropic.com/)
- [Google Gemini API](https://ai.google.dev/docs)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Python asyncio subprocess](https://docs.python.org/3/library/asyncio-subprocess.html)
- [Model Context Protocol (MCP)](https://modelcontextprotocol.io/)
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)

---

## 14. 변경 이력 (Changelog)

| 버전 | 날짜       | 작성자 | 변경 내용                                                                             |
| ---- | ---------- | ------ | ------------------------------------------------------------------------------------- |
| 0.1  | 2026-01-05 | -      | 초안 작성                                                                             |
| 0.2  | 2026-01-05 | -      | 세션 관리 기능 추가 (F4), 기술 스택에 uv/Redis 추가, 확장성 고려한 프로젝트 구조 변경 |
| 0.3  | 2026-01-05 | -      | MCP Server 지원 추가 (F5), MCP 명세 섹션 추가, 아키텍처 및 프로젝트 구조에 MCP 레이어 반영 |
| 0.4  | 2026-01-05 | -      | 문서 검토: 성공 지표/리스크에 MCP/Redis 항목 추가, API 명세 보완, workers 모듈 추가 |
