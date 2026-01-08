# LLM MCP Hub - Project Memory

## Project Overview
- **Name**: LLM MCP Hub
- **Purpose**: 여러 LLM 프로바이더(Claude, Gemini 등)를 subprocess 기반으로 통합하여 REST API 및 MCP 서버로 제공하는 허브 시스템
- **Key Goal**: 기존 Claude/Gemini 구독을 활용하여 n8n 등 API 연계 시 추가 비용 발생 절감

## Critical Constraints (전제조건)

> **API Key 방식 절대 사용 금지**

- Anthropic API Key, Google AI API Key 등 **LLM API Key 사용 금지**
- 이유: 사용량 기반 별도 비용 발생 → 구독 플랜 비용 절감 목적에 위배
- **CLI 기반 OAuth 인증**으로 기존 구독(Claude Pro/Max, Gemini Advanced) 활용
- Docker 컨테이너에서 CLI 인증 토큰 관리 → subprocess로 LLM CLI 실행

| 인증 방식 | 허용 | 비고 |
|-----------|------|------|
| Anthropic API Key | X | 사용량 과금 |
| Google AI API Key | X | 사용량 과금 |
| Claude CLI OAuth | O | 구독 플랜 활용 |
| Gemini CLI OAuth | O | 구독 플랜 활용 |
| Long-lived Access Token | O | CLI 인증 토큰 |

## Tech Stack
| Area | Technology | Reason |
|------|------------|--------|
| Language | Python 3.11+ | asyncio, subprocess 지원 |
| Package Manager | uv | 빠른 의존성 설치, lockfile 지원 |
| Framework | FastAPI | 비동기, OpenAPI 자동 생성 |
| MCP Server | mcp (Python SDK) | 공식 MCP Python SDK |
| Process Mgmt | asyncio.subprocess | 네이티브 비동기 subprocess |
| Config | Pydantic Settings | 타입 안전한 설정 관리 |
| Session Store | Redis | 분산 환경 지원, TTL 기반 만료 |

## Architecture Layers
1. **Presentation Layer**: REST API (FastAPI) + MCP Server (mcp SDK)
2. **Service Layer**: ChatService, SessionService
3. **Infrastructure Layer**: Session Store (Redis), Provider Registry, Worker Manager

## Key Features (Priority)
### P0 (Critical)
- Claude/Gemini subprocess 실행/관리
- REST API 엔드포인트 제공
- 요청 라우팅
- subprocess 생명주기 관리
- HTTP 헤더 기반 세션 ID (`X-Session-ID`)
- Redis 기반 세션 저장소
- 대화 기록 세션 저장
- MCP 서버 구현 (stdio/SSE)
- `chat` Tool 제공

### P1 (Important)
- Provider 상태 모니터링
- 스트리밍 응답 지원
- 인증/인가
- 프로세스 풀 관리
- 자동 재시작 (crash recovery)
- 세션 만료 관리 (TTL: 1시간)
- `list_providers`, `get_session` Tool

### P2 (Nice to Have)
- 동적 Provider 추가/제거
- 리소스 제한 (CPU, Memory)
- 세션 조회/삭제 API
- MCP Resources, Prompts

## API Endpoints
- `POST /v1/chat/completions` - 통합 채팅 완성 요청
- `GET /v1/sessions/{session_id}` - 세션 정보 조회
- `DELETE /v1/sessions/{session_id}` - 세션 삭제
- `GET /v1/providers` - Provider 목록
- `GET /health` - 헬스체크

## MCP Tools
- `chat` - LLM에 대화 요청
- `list_providers` - Provider 목록 조회
- `get_session` - 세션 정보 조회

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
│   ├── domain/              # 도메인 모델
│   ├── infrastructure/      # 외부 시스템 연동
│   │   ├── session/         # 세션 저장소 (Redis/Memory)
│   │   ├── providers/       # LLM Provider (Claude/Gemini)
│   │   └── workers/         # subprocess 관리
│   ├── api/v1/              # REST API
│   ├── mcp/                 # MCP Server
│   │   ├── tools/           # MCP Tools
│   │   ├── resources/       # MCP Resources
│   │   └── prompts/         # MCP Prompts
│   └── services/            # 비즈니스 서비스
└── tests/
```

## Design Principles
1. **계층 분리**: API → Services → Domain → Infrastructure
2. **의존성 역전**: Infrastructure는 인터페이스에 의존
3. **API 버전 관리**: `/api/v1/`, `/api/v2/` 확장 가능
4. **모듈화**: 새 Provider 추가 시 파일만 추가
5. **테스트 용이성**: 인메모리 구현체로 테스트 가능

## Development Phases
1. **Phase 1: Foundation** - 프로젝트 설정, FastAPI, Redis, subprocess 관리
2. **Phase 2: Provider Integration** - Claude/Gemini Provider, REST API
3. **Phase 3: MCP Server** - MCP 서버, Tools, Resources, stdio/SSE
4. **Phase 4: Production Ready** - 에러 핸들링, 로깅, 테스트, 문서화

## Success Metrics
- API 응답 시간: < 100ms (LLM 응답 제외)
- 가용성: 99.9%
- 지원 LLM: 2개 이상 (Claude, Gemini)
- MCP 클라이언트: Claude Desktop, Cursor 연동
- 세션 유지: 1시간 TTL
