# LLM MCP Hub - API 명세서

## 목차
1. [개요](#1-개요)
2. [인증](#2-인증)
3. [공통 규격](#3-공통-규격)
4. [REST API 엔드포인트](#4-rest-api-엔드포인트)
5. [MCP Server 명세](#5-mcp-server-명세)
6. [에러 코드](#6-에러-코드)

---

## 1. 개요

### 1.1 Base URL
```
http://localhost:8000
```

### 1.2 API 버전
- 현재 버전: `v1`
- 모든 REST API는 `/v1` 접두사를 사용

### 1.3 지원 프로토콜
| 프로토콜 | 용도 |
|----------|------|
| REST API | HTTP/HTTPS 기반 API 호출 |
| MCP (stdio) | Claude Desktop, 로컬 CLI 연동 |
| MCP (SSE) | 웹 기반 클라이언트, 원격 연동 |

---

## 2. 인증

### 2.1 허브 API 인증 (P1)
```http
Authorization: Bearer <hub-api-key>
```

> **Note**: 초기 버전에서는 인증 없이 사용 가능. P1에서 API Key 인증 추가 예정.

### 2.2 세션 관리 헤더
| 헤더 | 방향 | 필수 | 설명 |
|------|------|------|------|
| `X-Session-ID` | Request | 선택 | 기존 세션 ID. 없으면 새 세션 자동 생성 |
| `X-Session-ID` | Response | 항상 | 사용/생성된 세션 ID 반환 |

---

## 3. 공통 규격

### 3.1 요청 형식
- Content-Type: `application/json`
- 문자 인코딩: `UTF-8`

### 3.2 응답 형식
```json
{
  "success": true,
  "data": { ... },
  "error": null
}
```

### 3.3 에러 응답 형식
```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": { ... }
  }
}
```

### 3.4 페이지네이션 (해당 시)
```json
{
  "items": [...],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

### 3.5 타임스탬프 형식
- ISO 8601 형식: `2026-01-10T12:00:00Z`

---

## 4. REST API 엔드포인트

### 4.1 채팅 API

#### POST /v1/chat/completions
통합 채팅 완성 요청

**Request Headers**
```http
Content-Type: application/json
X-Session-ID: abc123-def456-... (optional)
```

**Request Body**
```json
{
  "provider": "claude",
  "model": "claude-sonnet-4-5-20250929",
  "messages": [
    {
      "role": "user",
      "content": "안녕하세요, 오늘 날씨가 어때요?"
    }
  ],
  "stream": false,
  "max_tokens": 1024,
  "temperature": 0.7
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `provider` | string | 선택 | `"auto"` | `"claude"`, `"gemini"`, `"auto"` (세션 사용 시 무시됨) |
| `model` | string | 선택 | Provider 기본값 | 사용할 모델 ID (세션 사용 시 무시됨) |
| `messages` | array | 필수 | - | 대화 메시지 배열 |
| `messages[].role` | string | 필수 | - | `"user"`, `"assistant"`, `"system"` |
| `messages[].content` | string | 필수 | - | 메시지 내용 |
| `stream` | boolean | 선택 | `false` | 스트리밍 응답 여부 |
| `max_tokens` | integer | 선택 | `1024` | 최대 응답 토큰 수 |
| `temperature` | float | 선택 | `0.7` | 응답 다양성 (0.0~1.0) |

**Provider 우선순위 규칙**

세션(`X-Session-ID`)을 사용하는 경우와 사용하지 않는 경우의 동작이 다릅니다:

| 상황 | provider/model 결정 |
|------|---------------------|
| 세션 없음 | 요청의 `provider`, `model` 사용 |
| 세션 있음 | **세션 생성 시 지정한 provider/model 사용** (요청 값 무시) |
| 세션 있음 + 다른 provider 요청 | 에러 반환 (`PROVIDER_MISMATCH`) |

> **주의**: 세션을 사용할 때는 세션 생성 시 설정한 `system_prompt`와 `context`가 해당 provider에 맞게 설정되어 있으므로, 다른 provider로 변경할 수 없습니다.

**Response Headers**
```http
Content-Type: application/json
X-Session-ID: abc123-def456-...
```

**Response Body (Non-streaming)**
```json
{
  "id": "chat-123456",
  "provider": "claude",
  "model": "claude-sonnet-4-5-20250929",
  "choices": [
    {
      "index": 0,
      "message": {
        "role": "assistant",
        "content": "안녕하세요! 저는 날씨 정보에 직접 접근할 수 없지만..."
      },
      "finish_reason": "stop"
    }
  ],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 42,
    "total_tokens": 57
  },
  "created_at": "2026-01-10T12:00:00Z"
}
```

**Response Body (Streaming, stream=true)**
```http
Content-Type: text/event-stream

data: {"id":"chat-123456","choices":[{"delta":{"content":"안녕"}}]}

data: {"id":"chat-123456","choices":[{"delta":{"content":"하세요"}}]}

data: {"id":"chat-123456","choices":[{"delta":{"content":"!"}}]}

data: [DONE]
```

---

### 4.2 세션 API

#### POST /v1/sessions
세션 생성 (컨텍스트 주입)

새 세션을 명시적으로 생성하고, 초기 컨텍스트(system prompt, 메모리 파일, 이전 세션 요약 등)를 주입합니다.

**Request Body**
```json
{
  "provider": "claude",
  "model": "claude-sonnet-4-5-20250929",
  "system_prompt": "당신은 Python 전문가입니다. 항상 타입 힌트를 사용하세요.",
  "context": {
    "memory": "# 프로젝트 컨텍스트\n- FastAPI 프로젝트\n- Redis 세션 저장소 사용\n...",
    "previous_summary": "이전 세션에서 인증 시스템 설계를 논의했습니다...",
    "files": [
      {
        "name": "CLAUDE.md",
        "content": "# Project Memory\n..."
      }
    ]
  },
  "ttl": 3600,
  "metadata": {
    "project": "llm-mcp-hub",
    "user": "developer"
  }
}
```

| 필드 | 타입 | 필수 | 기본값 | 설명 |
|------|------|------|--------|------|
| `provider` | string | 선택 | `"auto"` | `"claude"`, `"gemini"`, `"auto"` |
| `model` | string | 선택 | Provider 기본값 | 사용할 모델 ID |
| `system_prompt` | string | 선택 | - | 시스템 프롬프트 (AI 역할/지시사항) |
| `context` | object | 선택 | - | 초기 컨텍스트 정보 |
| `context.memory` | string | 선택 | - | 프로젝트 메모리 (CLAUDE.md 등) |
| `context.previous_summary` | string | 선택 | - | 이전 세션 요약 |
| `context.files` | array | 선택 | - | 참조 파일 목록 |
| `context.files[].name` | string | 필수 | - | 파일명 |
| `context.files[].content` | string | 필수 | - | 파일 내용 |
| `ttl` | integer | 선택 | `3600` | 세션 만료 시간 (초) |
| `metadata` | object | 선택 | - | 사용자 정의 메타데이터 |

**Response**
```json
{
  "session_id": "abc123-def456-ghi789",
  "provider": "claude",
  "model": "claude-sonnet-4-5-20250929",
  "has_system_prompt": true,
  "has_context": true,
  "context_summary": {
    "memory_chars": 1024,
    "previous_summary_chars": 256,
    "files_count": 1
  },
  "created_at": "2026-01-11T12:00:00Z",
  "expires_at": "2026-01-11T13:00:00Z",
  "metadata": {
    "project": "llm-mcp-hub",
    "user": "developer"
  }
}
```

**사용 예시: 컨텍스트 주입 후 대화**
```bash
# 1. 세션 생성 (컨텍스트 주입)
curl -X POST http://localhost:8000/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "claude",
    "system_prompt": "Python FastAPI 전문가로서 답변하세요.",
    "context": {
      "memory": "# 프로젝트 규칙\n- 타입 힌트 필수\n- Pydantic 사용"
    }
  }'

# Response: {"session_id": "abc123-def456", ...}

# 2. 생성된 세션으로 대화
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "X-Session-ID: abc123-def456" \
  -d '{
    "messages": [{"role": "user", "content": "세션 관리 코드 작성해줘"}]
  }'
```

**사용 예시: 이전 세션 요약 이월**
```bash
# 1. 이전 세션 요약 조회
SUMMARY=$(curl -s "http://localhost:8000/v1/sessions/old-session/memory?format=json" | jq -r '.summary')

# 2. 새 세션에 요약 주입
curl -X POST http://localhost:8000/v1/sessions \
  -H "Content-Type: application/json" \
  -d "{
    \"provider\": \"claude\",
    \"context\": {
      \"previous_summary\": \"$SUMMARY\"
    }
  }"
```

---

#### GET /v1/sessions/{session_id}
세션 정보 조회

**Path Parameters**
| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `session_id` | string | 세션 ID (UUID) |

**Response**
```json
{
  "session_id": "abc123-def456-ghi789",
  "status": "active",
  "provider": "claude",
  "model": "claude-sonnet-4-5-20250929",
  "system_prompt": "당신은 Python 전문가입니다.",
  "context": {
    "memory": "# 프로젝트 컨텍스트\n...",
    "previous_summary": "이전 세션 요약...",
    "files": [{"name": "CLAUDE.md", "content": "..."}]
  },
  "messages": [
    {
      "role": "user",
      "content": "안녕하세요",
      "timestamp": "2026-01-10T12:00:00Z"
    },
    {
      "role": "assistant",
      "content": "안녕하세요! 무엇을 도와드릴까요?",
      "timestamp": "2026-01-10T12:00:05Z"
    }
  ],
  "message_count": 2,
  "metadata": {
    "project": "llm-mcp-hub"
  },
  "created_at": "2026-01-10T12:00:00Z",
  "updated_at": "2026-01-10T12:00:05Z",
  "expires_at": "2026-01-10T13:00:00Z",
  "ttl_remaining": 3595
}
```

| 필드 | 설명 |
|------|------|
| `status` | 세션 상태: `active`, `closed`, `expired` |
| `system_prompt` | 세션 생성 시 설정한 시스템 프롬프트 |
| `context` | 세션 생성 시 주입한 컨텍스트 정보 |
| `ttl_remaining` | 만료까지 남은 시간 (초) |

#### DELETE /v1/sessions/{session_id}
세션 삭제

**Response**
```json
{
  "success": true,
  "message": "Session deleted successfully",
  "session_id": "abc123-def456-ghi789"
}
```

#### POST /v1/sessions/{session_id}/close
세션 종료 및 메모리 저장

세션을 명시적으로 종료하고, 압축된 메모리를 자동 생성하여 반환합니다.
TTL 만료 전에 호출하여 메모리를 안전하게 보존할 수 있습니다.

**Path Parameters**
| 파라미터 | 타입 | 설명 |
|----------|------|------|
| `session_id` | string | 세션 ID (UUID) |

**Request Body (optional)**
```json
{
  "compression": "medium",
  "provider": "claude",
  "save_to_storage": true
}
```

| 필드 | 타입 | 기본값 | 설명 |
|------|------|--------|------|
| `compression` | string | `"medium"` | 압축 레벨: `none`, `low`, `medium`, `high` |
| `provider` | string | 세션 provider | 요약에 사용할 Provider |
| `save_to_storage` | boolean | `true` | 메모리를 영구 저장소에 보관 여부 |

**Response**
```json
{
  "success": true,
  "session_id": "abc123-def456-ghi789",
  "status": "closed",
  "closed_at": "2026-01-10T12:30:00Z",
  "summary": {
    "message_count": 24,
    "duration_seconds": 1800,
    "topics": ["API 서버 구축", "Redis 연동"],
    "decisions": ["FastAPI 사용", "OAuth 인증"]
  },
  "compressed_memory": "# 세션 메모리 (압축)\n\n## 논의 주제\n...",
  "storage": {
    "saved": true,
    "storage_id": "mem-abc123",
    "expires_at": "2026-02-10T12:30:00Z"
  }
}
```

**사용 시나리오**
```bash
# 1. 세션 종료하고 압축 메모리 획득
RESPONSE=$(curl -X POST "http://localhost:8000/v1/sessions/abc123/close" \
  -H "Content-Type: application/json" \
  -d '{"compression": "medium"}')

# 2. 압축 메모리 추출
MEMORY=$(echo $RESPONSE | jq -r '.compressed_memory')

# 3. 새 세션에 바로 주입
curl -X POST http://localhost:8000/v1/sessions \
  -H "Content-Type: application/json" \
  -d "{\"context\": {\"previous_summary\": \"$MEMORY\"}}"
```

> **참고**: 종료된 세션은 더 이상 채팅에 사용할 수 없습니다. `GET /v1/sessions/{id}`로 조회는 가능하지만 `status`가 `closed`로 표시됩니다.

---

#### GET /v1/sessions/{session_id}/memory
세션 메모리 내보내기 (압축/요약 지원)

대화 기록을 압축하여 다음 세션에 이월하거나 백업용으로 내보냅니다.

**Query Parameters**
| 파라미터 | 타입 | 기본값 | 설명 |
|----------|------|--------|------|
| `compression` | string | `"medium"` | 압축 레벨: `"none"`, `"low"`, `"medium"`, `"high"` |
| `provider` | string | `"claude"` | 압축/요약에 사용할 Provider |
| `format` | string | `"markdown"` | 출력 형식: `"markdown"`, `"json"` |

**압축 레벨 설명**

| 레벨 | 출력 내용 | 용도 | 예상 크기 |
|------|-----------|------|-----------|
| `none` | 전체 대화 기록 (압축 없음) | 감사 로그, 전체 백업 | 100% |
| `low` | 요약 + 주요 메시지 발췌 | 상세 컨텍스트 이월 | ~30% |
| `medium` | 주제별 요약 + 결정사항 + 액션아이템 | 일반적인 컨텍스트 이월 | ~15% |
| `high` | 핵심 키워드, 결정사항만 | 토큰 절약, 빠른 컨텍스트 주입 | ~5% |

**Response (compression=none, format=markdown)**
```http
Content-Type: text/markdown; charset=utf-8
Content-Disposition: attachment; filename="session_abc123_20260110_120000.md"

# Session Memory: abc123-def456-ghi789

## 메타데이터
- **생성일시**: 2026-01-10 12:00:00
- **종료일시**: 2026-01-10 12:30:00
- **Provider**: Claude
- **총 메시지 수**: 24

## 대화 기록

### User (12:00:00)
Python으로 API 서버를 만들고 싶어요.

### Assistant (12:00:05)
FastAPI를 추천드립니다. FastAPI는 Python 3.7+에서 동작하며...

### User (12:00:30)
Redis는 어떻게 연결하나요?

### Assistant (12:00:35)
redis-py 라이브러리를 사용하면 됩니다...

---
*Generated by LLM MCP Hub*
```

**Response (compression=medium, format=markdown)** - 권장
```http
Content-Type: text/markdown; charset=utf-8

# 세션 메모리 (압축)

## 메타데이터
- **세션**: abc123-def456-ghi789
- **기간**: 2026-01-10 12:00 ~ 12:30
- **메시지 수**: 24개 → 압축됨

## 논의 주제
1. **API 서버 구축** - FastAPI 프레임워크 선택
2. **데이터베이스 연동** - Redis 세션 저장소 구성
3. **인증 시스템** - OAuth 토큰 기반 인증

## 결정사항
- [x] FastAPI + Pydantic 사용
- [x] Redis를 세션 저장소로 사용
- [x] Claude Agent SDK로 LLM 연동

## 사용자 선호/스타일
- 타입 힌트 필수
- 한국어 응답 선호
- 간결한 코드 스타일

## 다음 단계
- [ ] 프로젝트 초기 설정
- [ ] Redis 연결 테스트
- [ ] 기본 API 엔드포인트 구현

---
*Compressed by LLM MCP Hub*
```

**Response (compression=high, format=markdown)** - 최소 토큰
```http
Content-Type: text/markdown; charset=utf-8

# 핵심 컨텍스트

**프로젝트**: Python FastAPI API 서버
**스택**: FastAPI, Redis, Claude Agent SDK
**결정**: OAuth 인증, 타입힌트 필수, 한국어 응답
**진행**: API 명세 완료, 구현 예정

---
*Compressed by LLM MCP Hub*
```

**Response (compression=medium, format=json)**
```json
{
  "session_id": "abc123-def456-ghi789",
  "compression": "medium",
  "original_message_count": 24,
  "created_at": "2026-01-10T12:00:00Z",
  "ended_at": "2026-01-10T12:30:00Z",
  "provider": "claude",
  "topics": [
    {
      "title": "API 서버 구축",
      "summary": "FastAPI 프레임워크 선택"
    },
    {
      "title": "데이터베이스 연동",
      "summary": "Redis 세션 저장소 구성"
    }
  ],
  "decisions": [
    "FastAPI + Pydantic 사용",
    "Redis를 세션 저장소로 사용",
    "Claude Agent SDK로 LLM 연동"
  ],
  "user_preferences": {
    "language": "한국어",
    "code_style": "타입 힌트 필수",
    "response_style": "간결함"
  },
  "action_items": [
    "프로젝트 초기 설정",
    "Redis 연결 테스트"
  ],
  "compressed_memory": "# 핵심 컨텍스트\n**프로젝트**: Python FastAPI API 서버\n..."
}
```

**사용 예시: 세션 이월 워크플로우**
```bash
# 1. 현재 세션 메모리 압축 다운로드
MEMORY=$(curl -s "http://localhost:8000/v1/sessions/old-session/memory?compression=medium&format=json" \
  | jq -r '.compressed_memory')

# 2. 새 세션에 압축된 메모리 주입
curl -X POST http://localhost:8000/v1/sessions \
  -H "Content-Type: application/json" \
  -d "{
    \"provider\": \"claude\",
    \"context\": {
      \"previous_summary\": \"$MEMORY\"
    }
  }"

# 3. 이전 맥락을 기억한 상태로 대화 시작
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "X-Session-ID: new-session-id" \
  -d '{"messages": [{"role": "user", "content": "아까 얘기한 Redis 연결 코드 작성해줘"}]}'
```

---

### 4.3 Provider API

#### GET /v1/providers
사용 가능한 Provider 목록 조회

**Response**
```json
{
  "providers": [
    {
      "name": "claude",
      "display_name": "Claude",
      "status": "available",
      "models": [
        {
          "id": "claude-sonnet-4-5-20250929",
          "name": "Claude Sonnet 4.5",
          "default": true
        },
        {
          "id": "claude-opus-4-5-20250929",
          "name": "Claude Opus 4.5",
          "default": false
        }
      ],
      "auth_method": "oauth_token",
      "features": {
        "streaming": true,
        "session": true,
        "max_tokens": 8192
      }
    },
    {
      "name": "gemini",
      "display_name": "Gemini",
      "status": "available",
      "models": [
        {
          "id": "gemini-2.5-pro",
          "name": "Gemini 2.5 Pro",
          "default": true
        },
        {
          "id": "gemini-2.5-flash",
          "name": "Gemini 2.5 Flash",
          "default": false
        }
      ],
      "auth_method": "oauth_file",
      "features": {
        "streaming": false,
        "session": true,
        "max_tokens": 8192
      }
    }
  ]
}
```

#### GET /v1/providers/{provider_name}
특정 Provider 상세 정보 조회

**Response**
```json
{
  "name": "claude",
  "display_name": "Claude",
  "status": "available",
  "models": [...],
  "auth_method": "oauth_token",
  "features": {...},
  "health": {
    "latency_ms": 45,
    "last_check": "2026-01-10T12:00:00Z",
    "error_rate_1h": 0.01
  }
}
```

---

### 4.4 헬스체크 API

#### GET /health
시스템 헬스체크

**Response**
```json
{
  "status": "healthy",
  "version": "0.1.0",
  "uptime_seconds": 3600,
  "providers": {
    "claude": "up",
    "gemini": "up"
  },
  "dependencies": {
    "redis": "connected"
  },
  "timestamp": "2026-01-10T12:00:00Z"
}
```

| status 값 | 설명 |
|-----------|------|
| `healthy` | 모든 시스템 정상 |
| `degraded` | 일부 기능 제한 (예: Provider 1개 다운) |
| `unhealthy` | 서비스 불가 |

#### GET /health/tokens
OAuth 토큰 상태 확인

**Response**
```json
{
  "claude": {
    "status": "valid",
    "auth_method": "oauth_token",
    "expires_at": "2026-01-17T12:00:00Z",
    "days_remaining": 7,
    "message": null
  },
  "gemini": {
    "status": "warning",
    "auth_method": "oauth_file",
    "expires_at": "2026-01-13T12:00:00Z",
    "days_remaining": 3,
    "message": "Token expires soon, please refresh"
  }
}
```

| status 값 | 설명 |
|-----------|------|
| `valid` | 토큰 정상 (7일 이상 남음) |
| `warning` | 곧 만료 예정 (3~7일 남음) |
| `expiring` | 매우 긴급 (3일 미만) |
| `expired` | 만료됨 |
| `invalid` | 유효하지 않은 토큰 |

---

## 5. MCP Server 명세

### 5.1 서버 정보
```json
{
  "name": "llm-mcp-hub",
  "version": "0.1.0",
  "description": "Multi-LLM Hub - Access Claude, Gemini via unified interface"
}
```

### 5.2 Tools

#### create_session
세션 생성 (컨텍스트 주입)

**Input Schema**
```json
{
  "name": "create_session",
  "description": "Create a new session with optional context injection",
  "inputSchema": {
    "type": "object",
    "properties": {
      "provider": {
        "type": "string",
        "enum": ["claude", "gemini", "auto"],
        "default": "auto",
        "description": "LLM provider to use"
      },
      "system_prompt": {
        "type": "string",
        "description": "System prompt for AI role/instructions"
      },
      "context": {
        "type": "object",
        "description": "Initial context to inject",
        "properties": {
          "memory": {"type": "string", "description": "Project memory (e.g., CLAUDE.md content)"},
          "previous_summary": {"type": "string", "description": "Summary from previous session"}
        }
      },
      "ttl": {
        "type": "integer",
        "default": 3600,
        "description": "Session TTL in seconds"
      }
    }
  }
}
```

**Example Call**
```json
{
  "name": "create_session",
  "arguments": {
    "provider": "claude",
    "system_prompt": "Python 전문가로서 답변하세요.",
    "context": {
      "memory": "# 프로젝트 규칙\n- 타입 힌트 필수"
    }
  }
}
```

**Example Response**
```json
{
  "content": [{"type": "text", "text": "Session created: abc123-def456"}],
  "metadata": {
    "session_id": "abc123-def456",
    "provider": "claude",
    "expires_at": "2026-01-11T13:00:00Z"
  }
}
```

#### chat
LLM에 대화 요청

**Input Schema**
```json
{
  "name": "chat",
  "description": "Send a message to LLM and get a response",
  "inputSchema": {
    "type": "object",
    "properties": {
      "message": {
        "type": "string",
        "description": "User message to send"
      },
      "provider": {
        "type": "string",
        "enum": ["claude", "gemini", "auto"],
        "default": "auto",
        "description": "LLM provider to use (ignored if session_id provided)"
      },
      "session_id": {
        "type": "string",
        "description": "Session ID for conversation context (optional)"
      },
      "model": {
        "type": "string",
        "description": "Specific model to use (ignored if session_id provided)"
      }
    },
    "required": ["message"]
  }
}
```

**Example Call**
```json
{
  "name": "chat",
  "arguments": {
    "message": "Python에서 비동기 프로그래밍이란?",
    "provider": "claude"
  }
}
```

**Example Response**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Python의 비동기 프로그래밍은 asyncio 모듈을 사용하여..."
    }
  ],
  "metadata": {
    "provider": "claude",
    "model": "claude-sonnet-4-5-20250929",
    "session_id": "abc123-def456"
  }
}
```

#### list_providers
사용 가능한 Provider 목록 조회

**Input Schema**
```json
{
  "name": "list_providers",
  "description": "List available LLM providers and their status",
  "inputSchema": {
    "type": "object",
    "properties": {},
    "required": []
  }
}
```

**Example Response**
```json
{
  "content": [
    {
      "type": "text",
      "text": "Available providers:\n- claude (available): Claude Sonnet 4.5, Claude Opus 4.5\n- gemini (available): Gemini 2.5 Pro, Gemini 2.5 Flash"
    }
  ]
}
```

#### get_session
세션 정보 조회

**Input Schema**
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

#### export_session_memory
세션 메모리 내보내기

**Input Schema**
```json
{
  "name": "export_session_memory",
  "description": "Export session conversation with compression options",
  "inputSchema": {
    "type": "object",
    "properties": {
      "session_id": {
        "type": "string",
        "description": "Session ID to export"
      },
      "compression": {
        "type": "string",
        "enum": ["none", "low", "medium", "high"],
        "default": "medium",
        "description": "Compression level: none (full), low (~30%), medium (~15%), high (~5%)"
      },
      "provider": {
        "type": "string",
        "default": "claude",
        "description": "Provider to use for compression/summary"
      },
      "format": {
        "type": "string",
        "enum": ["markdown", "json"],
        "default": "markdown",
        "description": "Output format"
      }
    },
    "required": ["session_id"]
  }
}
```

**Example Call**
```json
{
  "name": "export_session_memory",
  "arguments": {
    "session_id": "abc123-def456",
    "compression": "medium"
  }
}
```

#### close_session
세션 종료 및 메모리 저장

**Input Schema**
```json
{
  "name": "close_session",
  "description": "Close session and save compressed memory",
  "inputSchema": {
    "type": "object",
    "properties": {
      "session_id": {
        "type": "string",
        "description": "Session ID to close"
      },
      "compression": {
        "type": "string",
        "enum": ["none", "low", "medium", "high"],
        "default": "medium",
        "description": "Compression level for memory"
      }
    },
    "required": ["session_id"]
  }
}
```

**Example Response**
```json
{
  "content": [{"type": "text", "text": "Session closed. Memory saved."}],
  "metadata": {
    "session_id": "abc123-def456",
    "status": "closed",
    "compressed_memory": "# 세션 메모리 (압축)\n..."
  }
}
```

### 5.3 Resources

| URI 패턴 | 설명 | MIME Type |
|----------|------|-----------|
| `provider://list` | 전체 Provider 목록 | `application/json` |
| `provider://{name}` | 특정 Provider 상세 정보 | `application/json` |
| `session://{session_id}` | 세션 정보 및 대화 기록 | `application/json` |

**Example: provider://claude**
```json
{
  "uri": "provider://claude",
  "name": "Claude Provider",
  "mimeType": "application/json",
  "contents": {
    "name": "claude",
    "status": "available",
    "models": ["claude-sonnet-4-5-20250929", "claude-opus-4-5-20250929"]
  }
}
```

### 5.4 Prompts (P2)

| 이름 | 설명 | Arguments |
|------|------|-----------|
| `summarize` | 대화 내용 요약 | `text`: 요약할 텍스트 |
| `translate` | 텍스트 번역 | `text`, `target_language` |
| `code_review` | 코드 리뷰 | `code`, `language` |

### 5.5 전송 방식

#### stdio (기본)
```bash
# 직접 실행
uv run llm-mcp-hub-server

# Claude Desktop 설정
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

#### SSE (Server-Sent Events)
```bash
# SSE 서버 실행
uv run llm-mcp-hub-server --transport sse --port 3001

# 클라이언트 연결
curl -N http://localhost:3001/sse
```

---

## 6. 에러 코드

### 6.1 HTTP 상태 코드

| 코드 | 설명 |
|------|------|
| 200 | 성공 |
| 201 | 생성됨 |
| 400 | 잘못된 요청 |
| 401 | 인증 필요 |
| 403 | 권한 없음 |
| 404 | 리소스 없음 |
| 429 | 요청 횟수 초과 |
| 500 | 서버 내부 오류 |
| 503 | 서비스 일시 불가 |

### 6.2 에러 코드 상세

| 코드 | HTTP | 설명 |
|------|------|------|
| `INVALID_REQUEST` | 400 | 요청 형식 오류 |
| `MISSING_FIELD` | 400 | 필수 필드 누락 |
| `INVALID_PROVIDER` | 400 | 지원하지 않는 Provider |
| `INVALID_MODEL` | 400 | 지원하지 않는 모델 |
| `PROVIDER_MISMATCH` | 400 | 세션과 다른 provider 요청 |
| `CONTEXT_TOO_LARGE` | 400 | 컨텍스트 크기 초과 (max 100KB) |
| `INVALID_COMPRESSION` | 400 | 잘못된 압축 레벨 |
| `UNAUTHORIZED` | 401 | 인증 실패 |
| `SESSION_NOT_FOUND` | 404 | 세션 없음 |
| `SESSION_EXPIRED` | 410 | 세션 만료됨 (TTL 초과) |
| `SESSION_CLOSED` | 410 | 이미 종료된 세션 |
| `PROVIDER_NOT_FOUND` | 404 | Provider 없음 |
| `RATE_LIMITED` | 429 | 요청 제한 초과 |
| `PROVIDER_UNAVAILABLE` | 503 | Provider 연결 불가 |
| `TOKEN_EXPIRED` | 503 | OAuth 토큰 만료 |
| `COMPRESSION_FAILED` | 500 | 메모리 압축 실패 |
| `INTERNAL_ERROR` | 500 | 내부 서버 오류 |

### 6.3 에러 응답 예시

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "SESSION_NOT_FOUND",
    "message": "Session with ID 'abc123' not found",
    "details": {
      "session_id": "abc123",
      "suggestion": "Create a new session by omitting X-Session-ID header"
    }
  }
}
```

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "TOKEN_EXPIRED",
    "message": "Claude OAuth token has expired",
    "details": {
      "provider": "claude",
      "expired_at": "2026-01-09T12:00:00Z",
      "action_required": "Please refresh the OAuth token"
    }
  }
}
```

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "PROVIDER_MISMATCH",
    "message": "Cannot use different provider for existing session",
    "details": {
      "session_provider": "claude",
      "requested_provider": "gemini",
      "suggestion": "Use the same provider as session or create a new session"
    }
  }
}
```

```json
{
  "success": false,
  "data": null,
  "error": {
    "code": "SESSION_CLOSED",
    "message": "Session has been closed",
    "details": {
      "session_id": "abc123",
      "closed_at": "2026-01-10T12:30:00Z",
      "suggestion": "Create a new session with the compressed memory"
    }
  }
}
```

---

## 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| 0.1 | 2026-01-10 | 초안 작성 - REST API, MCP Tools/Resources 명세 |
| 0.2 | 2026-01-11 | `POST /v1/sessions` 세션 생성 API 추가 - 컨텍스트 주입 지원 |
| 0.3 | 2026-01-11 | `GET /v1/sessions/{id}/memory` 압축 레벨 옵션 추가 (`compression` 파라미터) |
| 0.4 | 2026-01-11 | 설계 리뷰 반영: Provider 충돌 규칙, 세션 종료 API, MCP Tools 확장, 에러 코드 추가 |
