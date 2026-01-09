# LLM MCP Hub - Project Memory

## Project Overview
- **Name**: LLM MCP Hub
- **Purpose**: 여러 LLM 프로바이더(Claude, Gemini 등)를 **SDK/API 기반**으로 통합하여 REST API 및 MCP 서버로 제공하는 허브 시스템
- **Key Goal**: 기존 Claude/Gemini 구독을 활용하여 n8n 등 API 연계 시 추가 비용 발생 절감

## Critical Constraints (전제조건)

> **API Key 방식 절대 사용 금지**

- Anthropic API Key, Google AI API Key 등 **LLM API Key 사용 금지**
- 이유: 사용량 기반 별도 비용 발생 → 구독 플랜 비용 절감 목적에 위배
- **Claude Agent SDK + OAuth 토큰**으로 기존 구독(Claude Pro/Max) 활용
- **Gemini CLI + PTY 래퍼**로 기존 구독(Gemini Advanced) 활용
- Docker 컨테이너에서 OAuth 토큰을 환경변수로 관리

| 인증 방식 | 허용 | 비고 |
|-----------|------|------|
| Anthropic API Key | X | 사용량 과금 |
| Google AI API Key | X | 사용량 과금 |
| Google GenAI SDK (`google-genai`) | X | API 과금 기반, 구독 활용 불가 |
| Claude Agent SDK + OAuth Token | O | 구독 플랜 활용 (권장) |
| Gemini CLI + PTY Wrapper | O | 구독 플랜 활용 |
| `CLAUDE_CODE_OAUTH_TOKEN` 환경변수 | O | SDK 인증용 |

### Provider별 구현 방식 선택 이유

| Provider | 방식 | 이유 |
|----------|------|------|
| **Claude** | Agent SDK | 공식 SDK가 OAuth 토큰을 지원하고 구독 플랜 활용 가능, TTY 불필요 |
| **Gemini** | CLI + PTY | Google GenAI SDK는 API 과금 기반이라 구독 활용 불가, CLI만 구독 활용 가능 |

> **참고**: Google GenAI SDK (`pip install google-genai`)가 존재하지만, API Key 기반 과금 체계를 사용하므로 Gemini Advanced 구독을 활용할 수 없습니다. 따라서 CLI + PTY 래퍼 방식만 사용합니다.

## Tech Stack
| Area | Technology | Reason |
|------|------------|--------|
| Language | Python 3.11+ | asyncio, 타입 힌트 지원 |
| Package Manager | uv | 빠른 의존성 설치, lockfile 지원 |
| Framework | FastAPI | 비동기, OpenAPI 자동 생성 |
| **Claude Provider** | **claude-agent-sdk** | 공식 SDK, OAuth 지원, TTY 불필요 |
| **Gemini Provider** | **ptyprocess + gemini-cli** | PTY 래퍼로 CLI 제어 |
| MCP Server | mcp (Python SDK) | 공식 MCP Python SDK |
| Config | Pydantic Settings | 타입 안전한 설정 관리 |
| Session Store | Redis | 분산 환경 지원, TTL 기반 만료 |

## Architecture

### 시스템 구성도

```
┌─────────────────────────────────────────────────────────────────┐
│                         Clients                                  │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐  │
│  │  REST API       │  │  MCP Clients    │  │  n8n Workflow   │  │
│  │  (curl, etc.)   │  │  (Claude Desktop│  │                 │  │
│  │                 │  │   Cursor)       │  │                 │  │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘  │
└───────────┼─────────────────────┼─────────────────────┼─────────┘
            │                     │                     │
            ▼                     ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                        LLM MCP Hub                               │
├─────────────────────────────────────────────────────────────────┤
│  Presentation Layer                                              │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │ REST API (FastAPI)   │  │ MCP Server (stdio/SSE)           │ │
│  │ POST /v1/chat/...    │  │ Tools: chat, list_providers      │ │
│  │ GET  /v1/sessions/.. │  │ Resources: provider://, session://│ │
│  └──────────────────────┘  └──────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Service Layer                                                   │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │ ChatService          │  │ SessionService                   │ │
│  │ - route_to_provider  │  │ - create/get/delete session      │ │
│  │ - handle_streaming   │  │ - manage message history         │ │
│  └──────────────────────┘  └──────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Infrastructure Layer                                            │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐ │
│  │ Claude Adapter │  │ Gemini Adapter │  │ Session Store      │ │
│  │ (Agent SDK)    │  │ (PTY + CLI)    │  │ (Redis)            │ │
│  │                │  │                │  │                    │ │
│  │ OAuth Token    │  │ OAuth Token    │  │ TTL: 1 hour        │ │
│  │ 환경변수 인증  │  │ 파일 마운트    │  │                    │ │
│  └───────┬────────┘  └───────┬────────┘  └────────────────────┘ │
└──────────┼───────────────────┼──────────────────────────────────┘
           │                   │
           ▼                   ▼
    ┌─────────────┐     ┌─────────────┐
    │ Claude API  │     │ Gemini API  │
    │ (claude.ai) │     │ (Google)    │
    │ Pro/Max 구독│     │ Advanced 구독│
    └─────────────┘     └─────────────┘
```

### Architecture Layers
1. **Presentation Layer**: REST API (FastAPI) + MCP Server (mcp SDK)
2. **Service Layer**: ChatService, SessionService
3. **Infrastructure Layer**: Provider Adapters (Claude SDK, Gemini PTY), Session Store (Redis)

## Key Features (Priority)
### P0 (Critical)
- **Claude Agent SDK 통합** (OAuth 토큰 인증)
- **Gemini CLI PTY 래퍼** (OAuth 토큰 인증)
- REST API 엔드포인트 제공
- Provider 라우팅
- HTTP 헤더 기반 세션 ID (`X-Session-ID`)
- Redis 기반 세션 저장소
- 대화 기록 세션 저장
- MCP 서버 구현 (stdio/SSE)
- `chat` Tool 제공

### P1 (Important)
- Provider 상태 모니터링
- 스트리밍 응답 지원 (AsyncIterator)
- 인증/인가
- 토큰 만료 감지 및 알림
- 세션 만료 관리 (TTL: 1시간)
- `list_providers`, `get_session` Tool
- **세션 메모리 내보내기** (대화 요약 + 마크다운 다운로드)

### P2 (Nice to Have)
- 동적 Provider 추가/제거
- 리소스 제한 (CPU, Memory)
- 세션 조회/삭제 API
- MCP Resources, Prompts

## Claude Provider 구현 (Agent SDK)

### 환경변수
```bash
# OAuth 토큰 (필수)
CLAUDE_CODE_OAUTH_TOKEN=your-oauth-token-here

# 모델 선택 (선택)
CLAUDE_MODEL=claude-sonnet-4-5-20250929
```

### 코드 예시
```python
import anyio
from claude_agent_sdk import query, ClaudeSDKClient

# 단순 쿼리
async def simple_chat(prompt: str) -> str:
    result = []
    async for message in query(prompt=prompt):
        result.append(str(message))
    return "".join(result)

# 대화형 세션
async def interactive_chat():
    async with ClaudeSDKClient() as client:
        response = await client.send("Hello!")
        return response
```

## Gemini Provider 구현 (PTY Wrapper)

### TTY 문제와 해결책

Gemini CLI는 인터랙티브 터미널(TTY)을 요구합니다. Docker 컨테이너에서 subprocess로 CLI를 호출하면 TTY가 없어 오류가 발생합니다.

```
# 문제: subprocess.run()은 TTY를 제공하지 않음
subprocess.run(["gemini", "-p", "Hello"])  # TTY 오류 발생
```

**해결책**: `ptyprocess` 라이브러리로 가상 터미널(PTY)을 생성하여 CLI가 실제 터미널에서 실행되는 것처럼 동작하게 합니다.

### 환경변수
```bash
# OAuth 토큰 파일 경로 (필수)
GEMINI_AUTH_PATH=/mnt/auth/gemini/oauth_creds.json

# 모델 선택 (선택, 기본값: gemini-2.5-pro)
GEMINI_MODEL=gemini-2.5-pro
```

### 코드 예시
```python
import asyncio
from ptyprocess import PtyProcess

class GeminiPTYAdapter:
    def __init__(self, auth_path: str):
        self.auth_path = auth_path

    async def chat(self, prompt: str) -> str:
        # PtyProcess는 동기 코드이므로 asyncio.to_thread()로 래핑
        return await asyncio.to_thread(self._sync_chat, prompt)

    def _sync_chat(self, prompt: str) -> str:
        """동기 PTY 실행"""
        proc = PtyProcess.spawn(
            ["gemini", "-p", prompt],
            env={"HOME": "/root"}  # credentials 위치
        )
        output = ""
        while proc.isalive():
            try:
                output += proc.read(1024).decode()
            except EOFError:
                break
        return output
```

## MemoryService 구현

세션 대화를 요약하고 마크다운으로 내보내는 서비스입니다.

### 코드 예시
```python
from datetime import datetime
from typing import Optional
from dataclasses import dataclass

@dataclass
class SessionMemory:
    session_id: str
    created_at: datetime
    ended_at: Optional[datetime]
    provider: str
    message_count: int
    summary: Optional[str]
    messages: list[dict]

class MemoryService:
    def __init__(self, session_store, chat_service):
        self.session_store = session_store
        self.chat_service = chat_service

    async def export_memory(
        self,
        session_id: str,
        summarize: bool = True,
        provider: str = "claude"
    ) -> str:
        """세션을 마크다운 형식으로 내보내기"""
        session = await self.session_store.get(session_id)
        if not session:
            raise SessionNotFoundError(session_id)

        summary = None
        if summarize:
            summary = await self._generate_summary(session, provider)

        return self._format_markdown(session, summary)

    async def _generate_summary(self, session, provider: str) -> str:
        """LLM을 사용하여 대화 요약 생성"""
        prompt = f"""다음 대화를 요약해주세요. 주요 주제, 결정사항, 액션 아이템을 포함해주세요.

대화 내용:
{self._format_conversation(session.messages)}

요약:"""
        return await self.chat_service.chat(prompt, provider=provider)

    def _format_markdown(self, session, summary: Optional[str]) -> str:
        """세션을 마크다운 형식으로 변환"""
        lines = [
            f"# Session Memory: {session.id}",
            "",
            "## 메타데이터",
            f"- **생성일시**: {session.created_at}",
            f"- **Provider**: {session.provider}",
            f"- **총 메시지 수**: {len(session.messages)}",
            "",
        ]

        if summary:
            lines.extend(["## 요약", summary, ""])

        lines.append("## 대화 기록")
        for msg in session.messages:
            role = "User" if msg["role"] == "user" else "Assistant"
            lines.extend([
                "",
                f"### {role} ({msg['timestamp']})",
                msg["content"],
            ])

        lines.extend(["", "---", "*Generated by LLM MCP Hub*"])
        return "\n".join(lines)
```

## API Endpoints
- `POST /v1/chat/completions` - 통합 채팅 완성 요청
- `GET /v1/sessions/{session_id}` - 세션 정보 조회
- `DELETE /v1/sessions/{session_id}` - 세션 삭제
- `GET /v1/sessions/{session_id}/memory` - 세션 요약 마크다운 다운로드
- `GET /v1/providers` - Provider 목록
- `GET /health` - 헬스체크
- `GET /health/tokens` - OAuth 토큰 상태 확인

### 세션 메모리 다운로드 API

세션 종료 후 대화 내역을 요약하여 마크다운 파일로 다운로드하는 기능입니다.

#### Endpoint
```
GET /v1/sessions/{session_id}/memory
```

#### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `summarize` | bool | `true` | LLM을 사용하여 대화 요약 생성 여부 |
| `provider` | string | `claude` | 요약에 사용할 LLM Provider |
| `format` | string | `markdown` | 출력 형식 (`markdown`, `json`) |

#### Response
```http
Content-Type: text/markdown; charset=utf-8
Content-Disposition: attachment; filename="session_{session_id}_{timestamp}.md"
```

#### 마크다운 출력 형식
```markdown
# Session Memory: {session_id}

## 메타데이터
- **생성일시**: 2024-01-15 10:30:00
- **종료일시**: 2024-01-15 11:45:00
- **Provider**: Claude
- **총 메시지 수**: 24

## 요약
[LLM이 생성한 대화 요약 - 주요 주제, 결정사항, 액션 아이템 등]

## 대화 기록

### User (10:30:05)
첫 번째 사용자 메시지...

### Assistant (10:30:12)
첫 번째 어시스턴트 응답...

---
*Generated by LLM MCP Hub*
```

#### 활용 시나리오
1. **지식 베이스 구축**: 중요한 대화를 마크다운으로 저장하여 문서화
2. **컨텍스트 이월**: 새 세션 시작 시 이전 요약을 시스템 프롬프트로 제공
3. **감사 로그**: 대화 이력을 파일로 보관
4. **n8n 워크플로우**: 세션 종료 시 자동으로 Notion/Obsidian에 저장

## MCP Tools
- `chat` - LLM에 대화 요청
- `list_providers` - Provider 목록 조회
- `get_session` - 세션 정보 조회
- `export_session_memory` - 세션 요약을 마크다운으로 내보내기

## MCP Resources
- `provider://list` - Provider 목록
- `provider://{name}` - 특정 Provider 상세 정보
- `session://{session_id}` - 세션 정보 및 대화 기록

## Project Structure
```
llm-mcp-hub/
├── src/llm_mcp_hub/
│   ├── main.py              # FastAPI 앱 진입점
│   ├── core/                # 설정 및 공통 모듈
│   │   ├── config.py        # Pydantic Settings
│   │   ├── exceptions.py    # 커스텀 예외
│   │   └── dependencies.py  # DI 컨테이너
│   ├── domain/              # 도메인 모델
│   │   ├── message.py
│   │   └── session.py
│   ├── infrastructure/      # 외부 시스템 연동
│   │   ├── session/         # 세션 저장소 (Redis/Memory)
│   │   │   ├── base.py
│   │   │   ├── redis.py
│   │   │   └── memory.py
│   │   └── providers/       # LLM Provider Adapters
│   │       ├── base.py      # Provider 추상 클래스
│   │       ├── claude.py    # Claude Agent SDK Adapter
│   │       └── gemini.py    # Gemini PTY Adapter
│   ├── api/v1/              # REST API
│   │   ├── router.py
│   │   ├── chat.py
│   │   ├── sessions.py
│   │   └── providers.py
│   ├── mcp/                 # MCP Server
│   │   ├── server.py
│   │   ├── tools/
│   │   └── resources/
│   └── services/            # 비즈니스 서비스
│       ├── chat.py
│       ├── session.py
│       └── memory.py        # 세션 메모리 내보내기 서비스
└── tests/
```

## Design Principles
1. **계층 분리**: API → Services → Domain → Infrastructure
2. **의존성 역전**: Infrastructure는 인터페이스에 의존
3. **API 버전 관리**: `/api/v1/`, `/api/v2/` 확장 가능
4. **모듈화**: 새 Provider 추가 시 파일만 추가
5. **테스트 용이성**: 인메모리 구현체로 테스트 가능

## Development Phases
1. **Phase 1: Foundation** - 프로젝트 설정, FastAPI, Redis, Claude SDK 연동
2. **Phase 2: Provider Integration** - Gemini PTY Adapter, REST API
3. **Phase 3: MCP Server** - MCP 서버, Tools, Resources, stdio/SSE
4. **Phase 4: Production Ready** - 에러 핸들링, 로깅, 테스트, 문서화

## Success Metrics
- API 응답 시간: < 100ms (LLM 응답 제외)
- 가용성: 99.9%
- 지원 LLM: 2개 이상 (Claude, Gemini)
- MCP 클라이언트: Claude Desktop, Cursor 연동
- 세션 유지: 1시간 TTL
- 토큰 갱신 주기: 1~2주 (알림 자동화)
