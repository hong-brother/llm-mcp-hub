# LLM MCP Hub - Project Memory

## Project Overview
- **Name**: LLM MCP Hub
- **Purpose**: 여러 LLM 프로바이더(Claude, Gemini 등)를 **CLI 기반**으로 통합하여 REST API 및 MCP 서버로 제공하는 허브 시스템
- **Key Goal**: 기존 Claude/Gemini 구독을 활용하여 n8n 등 API 연계 시 추가 비용 발생 절감

## Critical Constraints (전제조건)

> **API Key 방식 절대 사용 금지**

- Anthropic API Key, Google AI API Key 등 **LLM API Key 사용 금지**
- 이유: 사용량 기반 별도 비용 발생 → 구독 플랜 비용 절감 목적에 위배
- **claude-code CLI + OAuth 토큰**으로 기존 구독(Claude Pro/Max) 활용
- **Gemini CLI + PTY 래퍼**로 기존 구독(Gemini Advanced) 활용
- Docker 컨테이너에서 OAuth 토큰을 시크릿으로 관리

| 인증 방식 | 허용 | 비고 |
|-----------|------|------|
| Anthropic API Key | X | 사용량 과금 |
| Google AI API Key | X | 사용량 과금 |
| Google GenAI SDK (`google-genai`) | X | API 과금 기반, 구독 활용 불가 |
| **claude-code CLI + OAuth Token** | O | 구독 플랜 활용 (권장) |
| **Gemini CLI + PTY Wrapper** | O | 구독 플랜 활용 |
| `CLAUDE_CODE_OAUTH_TOKEN` 환경변수 | O | CLI 인증용 |

### Provider별 구현 방식 선택 이유

| Provider | 방식 | 이유 |
|----------|------|------|
| **Claude** | claude-code CLI | 공식 CLI가 `--output-format json` 지원, OAuth 토큰 인증, subprocess로 충분 |
| **Gemini** | CLI + PTY | Google GenAI SDK는 API 과금 기반이라 구독 활용 불가, CLI는 TTY 필요하여 PTY 래퍼 사용 |

> **참고**: Google GenAI SDK (`pip install google-genai`)가 존재하지만, API Key 기반 과금 체계를 사용하므로 Gemini Advanced 구독을 활용할 수 없습니다. 따라서 CLI + PTY 래퍼 방식만 사용합니다.

## Tech Stack
| Area | Technology | Reason |
|------|------------|--------|
| Language | Python 3.11+ | asyncio, 타입 힌트 지원 |
| Package Manager | uv | 빠른 의존성 설치, lockfile 지원 |
| Framework | FastAPI | 비동기, OpenAPI 자동 생성 |
| **Claude Provider** | **claude-code CLI** | `--output-format json` 지원, OAuth 인증 |
| **Gemini Provider** | **ptyprocess + gemini-cli** | PTY 래퍼로 CLI 제어 |
| MCP Server | mcp (Python SDK) | 공식 MCP Python SDK |
| Config | Pydantic Settings | 타입 안전한 설정 관리 |
| Session Store | Redis | 분산 환경 지원, TTL 기반 만료 |
| Secrets | Docker Secrets / 환경변수 | 계층적 시크릿 로더 |

## Environment Variables

| 변수 | 필수 | 기본값 | 설명 |
|------|------|--------|------|
| `CLAUDE_CODE_OAUTH_TOKEN` | O | - | Claude OAuth 토큰 |
| `CLAUDE_DEFAULT_MODEL` | X | `claude-sonnet-4-5-20250929` | Claude 기본 모델 |
| `GEMINI_AUTH_PATH` | O | - | Gemini OAuth 인증 파일 경로 |
| `GEMINI_DEFAULT_MODEL` | X | `gemini-2.5-pro` | Gemini 기본 모델 |
| `REDIS_URL` | X | `redis://localhost:6379` | Redis 연결 URL |
| `SESSION_TTL` | X | `3600` | 세션 만료 시간 (초) |
| `LOG_LEVEL` | X | `INFO` | 로그 레벨 |
| `SECRETS_PATH` | X | - | 커스텀 시크릿 파일 경로 |

## CLI Verification Summary (검증 완료)

### Claude CLI (`claude-code`)
| 옵션 | 지원 | 비고 |
|------|------|------|
| `-p, --print` | ✅ | 파이프용 출력 모드 |
| `--output-format json` | ✅ | 응답 완료 후 JSON 출력 |
| `--output-format stream-json` | ✅ | 실시간 스트리밍 (**--verbose 필수**) |
| `--model <model>` | ✅ | alias(`sonnet`) 또는 full name 지정 |
| `--list-models` | ❌ | **미지원** → 하드코딩 필요 |

### Gemini CLI
| 옵션 | 지원 | 비고 |
|------|------|------|
| `-p` | ✅ | 프롬프트 전달 |
| `-m` | ✅ | 모델 지정 |
| JSON 출력 | ❌ | **미지원** → PTY + ANSI 파싱 |
| TTY 필요 | ✅ | subprocess 불가 → PTY 필수 |

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
│  │ (claude-code)  │  │ (PTY + CLI)    │  │ (Redis)            │ │
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
3. **Infrastructure Layer**: Provider Adapters (Claude CLI, Gemini PTY), Session Store (Redis)

## Key Features (Priority)
### P0 (Critical)
- **claude-code CLI 통합** (OAuth 토큰 인증)
- **Gemini CLI PTY 래퍼** (OAuth 토큰 인증)
- REST API 엔드포인트 제공
- Provider 라우팅
- HTTP 헤더 기반 세션 ID (`X-Session-ID`)
- Redis 기반 세션 저장소
- 대화 기록 세션 저장
- MCP 서버 구현 (stdio/SSE)
- `chat` Tool 제공
- **세션 생성 API** (`POST /v1/sessions`) - 컨텍스트 주입 지원

### P1 (Important)
- Provider 상태 모니터링
- 스트리밍 응답 지원 (AsyncIterator)
- 인증/인가
- 토큰 만료 감지 및 알림
- 세션 만료 관리 (TTL: 1시간)
- `list_providers`, `get_session` Tool
- **세션 메모리 압축 내보내기** (압축 레벨: none/low/medium/high)

### P2 (Nice to Have)
- 동적 Provider 추가/제거
- 리소스 제한 (CPU, Memory)
- MCP Resources, Prompts

## Claude Provider 구현 (claude-code CLI)

### 환경변수
```bash
# OAuth 토큰 (필수)
CLAUDE_CODE_OAUTH_TOKEN=your-oauth-token-here

# 기본 모델 (선택, 세션 생성 시 지정 가능)
CLAUDE_DEFAULT_MODEL=claude-sonnet-4-5-20250929
```

### 지원 모델 조회 방식
- **하드코딩된 목록 사용**
- 이유: claude-code CLI는 `--list-models` 옵션을 지원하지 않음

| 모델 | Alias | 설명 |
|------|-------|------|
| `claude-sonnet-4-5-20250929` | `sonnet` | 균형잡힌 성능 (기본값) |
| `claude-opus-4-5-20251101` | `opus` | 최고 성능 |
| `claude-haiku-4-5-20251001` | `haiku` | 빠른 응답 |

> **참고**: CLI에서 `--model sonnet` 처럼 alias로도 지정 가능

### CLI 출력 형식

#### `--output-format json` (동기, 응답 완료 후 출력)
```json
{
  "type": "result",
  "subtype": "success",
  "is_error": false,
  "result": "응답 내용",
  "session_id": "uuid",
  "duration_ms": 4044,
  "total_cost_usd": 0.153
}
```

#### `--output-format stream-json --verbose` (비동기, 실시간 스트리밍)
```json
{"type":"system","subtype":"init","session_id":"...","model":"claude-opus-4-5-20251101"}
{"type":"assistant","message":{"content":[{"type":"text","text":"Hello..."}]}}
{"type":"assistant","message":{"content":[{"type":"text","text":" world!"}]}}
{"type":"result","subtype":"success","result":"Hello world!","duration_ms":1234}
```

| 형식 | 용도 | 특징 |
|------|------|------|
| `json` | API 서버, 배치 처리 | 응답 완료 후 한 번에 출력 |
| `stream-json` | 채팅 UI, 실시간 표시 | 토큰 단위 실시간 출력, **--verbose 필수** |

### 코드 예시
```python
import asyncio
import subprocess
import json
import os
import logging
from typing import AsyncIterator

logger = logging.getLogger(__name__)

class ClaudeCodeAdapter:
    """claude-code CLI 래퍼 - 하드코딩된 모델 목록 사용"""

    # 하드코딩된 모델 목록 (CLI가 --list-models 미지원)
    SUPPORTED_MODELS = [
        "claude-sonnet-4-5-20250929",
        "claude-opus-4-5-20251101",
        "claude-haiku-4-5-20251001",
    ]

    # 모델 alias 매핑
    MODEL_ALIASES = {
        "sonnet": "claude-sonnet-4-5-20250929",
        "opus": "claude-opus-4-5-20251101",
        "haiku": "claude-haiku-4-5-20251001",
    }

    def __init__(self, oauth_token: str, default_model: str | None = None):
        self.oauth_token = oauth_token
        self.supported_models: list[str] = []
        self.default_model = default_model

    async def initialize(self) -> None:
        """서버 시작 시 호출 - 하드코딩된 모델 목록 로드"""
        self.supported_models = self.SUPPORTED_MODELS.copy()

        if not self.default_model and self.supported_models:
            self.default_model = self.supported_models[0]

        logger.info(f"Claude initialized with models: {self.supported_models}")

    def _resolve_model(self, model: str | None) -> str:
        """모델명 또는 alias를 실제 모델명으로 변환"""
        if model is None:
            return self.default_model

        # alias인 경우 변환
        if model in self.MODEL_ALIASES:
            return self.MODEL_ALIASES[model]

        return model

    async def chat(self, prompt: str, model: str | None = None, timeout: float = 120.0) -> str:
        """단일 응답 (타임아웃 포함)"""
        effective_model = self._resolve_model(model)

        if effective_model not in self.supported_models:
            raise InvalidModelError(f"Unsupported model: {effective_model}")

        cmd = ["claude", "-p", prompt, "--output-format", "json", "--model", effective_model]

        try:
            result = await asyncio.wait_for(
                asyncio.to_thread(
                    subprocess.run,
                    cmd,
                    capture_output=True,
                    text=True,
                    env={**os.environ, "CLAUDE_CODE_OAUTH_TOKEN": self.oauth_token}
                ),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise ProviderTimeoutError("Claude", timeout)

        if result.returncode != 0:
            raise ProviderError(f"claude-code failed: {result.stderr}")

        response = json.loads(result.stdout)

        # 에러 응답 처리
        if response.get("is_error"):
            raise ProviderError(f"Claude error: {response.get('result', 'Unknown error')}")

        return response.get("result", "")

    async def chat_stream(self, prompt: str, model: str | None = None) -> AsyncIterator[str]:
        """스트리밍 응답 (--verbose 필수)"""
        effective_model = self._resolve_model(model)

        # 스트리밍은 --verbose 옵션 필요
        cmd = [
            "claude", "-p", prompt,
            "--output-format", "stream-json",
            "--verbose",
            "--model", effective_model
        ]

        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            env={**os.environ, "CLAUDE_CODE_OAUTH_TOKEN": self.oauth_token}
        )

        async for line in proc.stdout:
            if line:
                try:
                    data = json.loads(line.decode())
                    # assistant 메시지에서 텍스트 추출
                    if data.get("type") == "assistant":
                        message = data.get("message", {})
                        for content in message.get("content", []):
                            if content.get("type") == "text":
                                yield content.get("text", "")
                except json.JSONDecodeError:
                    continue

        await proc.wait()
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

# 기본 모델 (선택, 세션 생성 시 지정 가능)
GEMINI_DEFAULT_MODEL=gemini-2.5-pro
```

### 지원 모델 조회 방식
- **하드코딩된 목록 사용**
- 이유: Gemini CLI는 JSON 출력 미지원, ANSI 코드 파싱이 불안정하여 동적 조회 부적합

| 모델 | 설명 |
|------|------|
| `gemini-2.5-pro` | 최고 성능 (기본값) |
| `gemini-2.5-flash` | 빠른 응답 |
| `gemini-2.0-flash` | 경량 모델 |

### 코드 예시
```python
import asyncio
import re
import logging
from ptyprocess import PtyProcess

logger = logging.getLogger(__name__)

class GeminiPTYAdapter:
    """Gemini CLI PTY 래퍼 - 하드코딩된 모델 목록 사용"""

    ANSI_ESCAPE = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

    # 하드코딩된 모델 목록 (CLI 파싱 불안정으로 동적 조회 미사용)
    SUPPORTED_MODELS = [
        "gemini-2.5-pro",
        "gemini-2.5-flash",
        "gemini-2.0-flash",
    ]

    def __init__(self, auth_path: str, default_model: str | None = None):
        self.auth_path = auth_path
        self.supported_models: list[str] = []
        self.default_model = default_model

    async def initialize(self) -> None:
        """서버 시작 시 호출 - 하드코딩된 모델 목록 로드"""
        self.supported_models = self.SUPPORTED_MODELS.copy()

        if not self.default_model and self.supported_models:
            self.default_model = self.supported_models[0]

        logger.info(f"Gemini initialized with models: {self.supported_models}")

    async def chat(self, prompt: str, model: str | None = None, timeout: float = 120.0) -> str:
        """타임아웃이 있는 채팅"""
        effective_model = model or self.default_model

        if effective_model not in self.supported_models:
            raise InvalidModelError(f"Unsupported model: {effective_model}")

        try:
            return await asyncio.wait_for(
                asyncio.to_thread(self._sync_chat, prompt, effective_model),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise ProviderTimeoutError("Gemini", timeout)

    def _sync_chat(self, prompt: str, model: str) -> str:
        """동기 PTY 실행"""
        proc = PtyProcess.spawn(
            ["gemini", "-p", prompt, "-m", model],
            env={"HOME": "/root", "TERM": "dumb"}  # ANSI 코드 최소화
        )

        output = []
        while proc.isalive():
            try:
                chunk = proc.read(1024)
                output.append(chunk.decode('utf-8', errors='ignore'))
            except EOFError:
                break

        raw_output = ''.join(output)
        return self._parse_response(raw_output)

    def _parse_response(self, raw: str) -> str:
        """ANSI 코드 제거 및 응답 추출"""
        clean = self.ANSI_ESCAPE.sub('', raw)
        # CLI 출력 형식에 따라 추가 파싱 필요
        return clean.strip()
```

## Provider 초기화 (FastAPI Lifespan)

서버 시작 시 모든 Provider를 초기화하여 모델 목록을 로드합니다.

```python
# src/llm_mcp_hub/main.py
from contextlib import asynccontextmanager
import logging

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """서버 시작/종료 시 실행"""
    # 시작 시: Provider 초기화
    logger.info("Initializing providers...")

    try:
        await claude_adapter.initialize()  # 하드코딩 로드
        await gemini_adapter.initialize()  # 하드코딩 로드

        logger.info(f"Claude models: {claude_adapter.supported_models}")
        logger.info(f"Gemini models: {gemini_adapter.supported_models}")
        logger.info("All providers initialized successfully")
    except Exception as e:
        logger.error(f"Provider initialization failed: {e}")
        raise

    yield

    # 종료 시: 정리 작업
    logger.info("Shutting down...")

app = FastAPI(lifespan=lifespan)
```

### Provider별 모델 조회 방식 요약

| Provider | 조회 방식 | 이유 |
|----------|-----------|------|
| **Claude** | 하드코딩 | CLI가 `--list-models` 미지원 |
| **Gemini** | 하드코딩 | CLI 출력 파싱 불안정 |

> **참고**: 두 Provider 모두 하드코딩 방식 사용. 모델 추가/변경 시 `SUPPORTED_MODELS` 업데이트 필요.

## 보안: 토큰 저장 방식

### 계층적 시크릿 로더

환경에 따라 적절한 방식으로 시크릿을 로드합니다.

```python
# src/llm_mcp_hub/core/secrets.py
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import os
import json

class SecretProvider(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[str]:
        pass

class EnvSecretProvider(SecretProvider):
    """환경변수에서 시크릿 로드"""
    def get(self, key: str) -> Optional[str]:
        return os.environ.get(key)

class FileSecretProvider(SecretProvider):
    """파일에서 시크릿 로드 (Docker Secrets 호환)"""
    def __init__(self, base_path: str = "/run/secrets"):
        self.base_path = Path(base_path)

    def get(self, key: str) -> Optional[str]:
        # 환경변수로 파일 경로가 지정된 경우
        file_path_env = os.environ.get(f"{key}_FILE")
        if file_path_env:
            path = Path(file_path_env)
        else:
            path = self.base_path / key.lower()

        if path.exists():
            content = path.read_text().strip()
            if path.suffix == ".json":
                return json.loads(content)
            return content
        return None

class ChainedSecretProvider(SecretProvider):
    """여러 Provider를 순차적으로 시도"""
    def __init__(self, providers: list[SecretProvider]):
        self.providers = providers

    def get(self, key: str) -> Optional[str]:
        for provider in self.providers:
            value = provider.get(key)
            if value is not None:
                return value
        return None

def create_secret_provider() -> SecretProvider:
    """환경에 따라 적절한 시크릿 프로바이더 생성"""
    providers = []

    # 1순위: Docker Secrets
    if Path("/run/secrets").exists():
        providers.append(FileSecretProvider("/run/secrets"))

    # 2순위: 커스텀 시크릿 경로
    if os.environ.get("SECRETS_PATH"):
        providers.append(FileSecretProvider(os.environ["SECRETS_PATH"]))

    # 3순위: 환경변수 (fallback)
    providers.append(EnvSecretProvider())

    return ChainedSecretProvider(providers)
```

### 환경별 권장 방식

| 환경 | 권장 방식 | 설정 예시 |
|------|-----------|-----------|
| **로컬 개발** | `.env` 파일 + gitignore | `CLAUDE_CODE_OAUTH_TOKEN=xxx` |
| **Docker Compose** | Docker Secrets | `secrets: [claude_token]` |
| **Kubernetes** | K8s Secrets | `secretKeyRef` |
| **프로덕션** | Vault / AWS Secrets Manager | 중앙 관리 + 자동 로테이션 |

### 토큰 보안 체크리스트

| 항목 | 구현 방법 |
|------|-----------|
| **저장 시 암호화** | Docker Secrets (tmpfs), Vault |
| **전송 시 암호화** | HTTPS only |
| **접근 제어** | 파일 권한 600, non-root 실행 |
| **로그 마스킹** | TokenMaskingFilter 적용 |
| **만료 모니터링** | `/health/tokens` 엔드포인트 |

### 토큰 로깅 방지

```python
import re
import logging

class TokenMaskingFilter(logging.Filter):
    """로그에서 토큰 패턴 마스킹"""
    PATTERNS = [
        (r'eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+', '[JWT_MASKED]'),
        (r'oauth_token["\']?\s*[:=]\s*["\']?[\w-]+', 'oauth_token=[MASKED]'),
        (r'CLAUDE_CODE_OAUTH_TOKEN=\S+', 'CLAUDE_CODE_OAUTH_TOKEN=[MASKED]'),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, replacement in self.PATTERNS:
                record.msg = re.sub(pattern, replacement, record.msg)
        return True
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
- `POST /v1/sessions` - **세션 생성 (컨텍스트 주입)**
- `GET /v1/sessions/{session_id}` - 세션 정보 조회
- `POST /v1/sessions/{session_id}/close` - **세션 종료 및 메모리 저장**
- `DELETE /v1/sessions/{session_id}` - 세션 삭제
- `GET /v1/sessions/{session_id}/memory` - **세션 메모리 압축 다운로드**
- `GET /v1/providers` - Provider 목록
- `GET /v1/providers/{name}` - Provider 상세 정보
- `GET /v1/providers/{name}/models` - **Provider별 지원 모델 목록**
- `GET /health` - 헬스체크
- `GET /health/tokens` - OAuth 토큰 상태 확인

### Provider/Model 우선순위 규칙

| 상황 | provider 결정 | model 결정 |
|------|---------------|------------|
| 세션 없음 | 요청의 `provider` 사용 | 요청의 `model` 사용 |
| 세션 있음 | **세션의 provider 고정** | **요청의 model 사용** (같은 provider 내) |
| 세션 있음 + 다른 provider 요청 | 에러 (`PROVIDER_MISMATCH`) | - |
| 세션 있음 + 지원하지 않는 model | - | 에러 (`INVALID_MODEL`) |

> **핵심**: 세션 내에서 Provider는 변경 불가, Model은 해당 Provider가 지원하는 범위 내에서 자유롭게 변경 가능

### 예시 흐름

```bash
# 1. Gemini 세션 생성
POST /v1/sessions
{"provider": "gemini", "model": "gemini-2.5-pro"}
→ session_id: "sess_abc123"

# 2. 첫 요청 - gemini-2.5-pro
POST /v1/chat/completions
X-Session-ID: sess_abc123
{"messages": [...], "model": "gemini-2.5-pro"}
→ ✅ 정상

# 3. 두 번째 요청 - gemini-2.5-flash (빠른 응답 필요)
POST /v1/chat/completions
X-Session-ID: sess_abc123
{"messages": [...], "model": "gemini-2.5-flash"}
→ ✅ 정상 (같은 provider 내 모델 변경)

# 4. Claude로 변경 시도
POST /v1/chat/completions
X-Session-ID: sess_abc123
{"messages": [...], "provider": "claude"}
→ ❌ PROVIDER_MISMATCH 에러
```

### 세션 생성 API (컨텍스트 주입)

세션 시작 시 개인화된 컨텍스트를 주입하는 기능입니다.

#### Endpoint
```
POST /v1/sessions
```

#### Request Body
```json
{
  "provider": "claude",
  "model": "claude-sonnet-4-5-20250929",
  "system_prompt": "당신은 Python 전문가입니다.",
  "context": {
    "memory": "# 프로젝트 컨텍스트\n- FastAPI 프로젝트\n...",
    "previous_summary": "이전 세션 요약...",
    "files": [{"name": "CLAUDE.md", "content": "..."}]
  },
  "ttl": 3600,
  "metadata": {"project": "llm-mcp-hub"}
}
```

| 필드 | 설명 |
|------|------|
| `provider` | LLM Provider (필수): `claude`, `gemini` |
| `model` | 기본 모델 (선택): 해당 provider의 지원 모델 |
| `system_prompt` | AI 역할/지시사항 |
| `context.memory` | 프로젝트 메모리 (CLAUDE.md 등) |
| `context.previous_summary` | 이전 세션 요약 이월 |
| `context.files` | 참조 파일 목록 |
| `ttl` | 세션 만료 시간 (초, 기본 3600) |

#### Response
```json
{
  "session_id": "sess_abc123",
  "provider": "claude",
  "model": "claude-sonnet-4-5-20250929",
  "supported_models": [
    "claude-sonnet-4-5-20250929",
    "claude-opus-4-5-20251101",
    "claude-haiku-4-5-20251001"
  ],
  "created_at": "2024-01-01T00:00:00Z",
  "expires_at": "2024-01-01T01:00:00Z"
}
```

#### 사용 예시
```bash
# 1. 세션 생성 (컨텍스트 주입)
curl -X POST http://localhost:8000/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"provider": "claude", "context": {"memory": "# 프로젝트 규칙\n..."}}'

# 2. 생성된 세션으로 대화 (기본 모델)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "X-Session-ID: sess_abc123" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "질문..."}]}'

# 3. 같은 세션에서 다른 모델 사용 (alias 또는 full name)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "X-Session-ID: sess_abc123" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "간단한 질문"}], "model": "haiku"}'
```

### 세션 메모리 압축 다운로드 API

대화 기록을 압축하여 다음 세션에 이월하거나 백업용으로 내보냅니다.

#### Endpoint
```
GET /v1/sessions/{session_id}/memory
```

#### Query Parameters
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `compression` | string | `medium` | 압축 레벨: `none`, `low`, `medium`, `high` |
| `provider` | string | `claude` | 압축/요약에 사용할 LLM Provider |
| `format` | string | `markdown` | 출력 형식: `markdown`, `json` |

#### 압축 레벨
| 레벨 | 출력 내용 | 예상 크기 | 용도 |
|------|-----------|-----------|------|
| `none` | 전체 대화 기록 | 100% | 감사 로그, 백업 |
| `low` | 요약 + 주요 메시지 | ~30% | 상세 컨텍스트 |
| `medium` | 주제별 요약 + 결정사항 | ~15% | **일반 이월 (권장)** |
| `high` | 핵심 키워드만 | ~5% | 토큰 절약 |

#### 압축 결과 예시 (compression=medium)
```markdown
# 세션 메모리 (압축)

## 논의 주제
1. **API 서버 구축** - FastAPI 선택
2. **데이터베이스** - Redis 세션 저장소

## 결정사항
- [x] FastAPI + Pydantic 사용
- [x] Redis 세션 저장소

## 사용자 선호
- 타입 힌트 필수
- 한국어 응답

## 다음 단계
- [ ] 프로젝트 초기 설정
```

#### 세션 이월 워크플로우
```bash
# 1. 이전 세션 메모리 압축
MEMORY=$(curl -s "http://localhost:8000/v1/sessions/old-session/memory?compression=medium&format=json" \
  | jq -r '.compressed_memory')

# 2. 새 세션에 주입
curl -X POST http://localhost:8000/v1/sessions \
  -H "Content-Type: application/json" \
  -d "{\"provider\": \"claude\", \"context\": {\"previous_summary\": \"$MEMORY\"}}"

# 3. 이전 맥락 기억한 상태로 대화
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "X-Session-ID: new-session" \
  -H "Content-Type: application/json" \
  -d '{"messages": [{"role": "user", "content": "아까 얘기한 Redis 코드 작성해줘"}]}'
```

#### 활용 시나리오
1. **컨텍스트 이월**: 세션 종료 → 압축 → 다음 세션에 주입
2. **지식 베이스 구축**: 마크다운으로 저장하여 문서화
3. **감사 로그**: 대화 이력 파일 보관
4. **n8n 워크플로우**: 세션 종료 시 자동으로 Notion/Obsidian에 저장

### 세션 종료 API

세션을 명시적으로 종료하고 압축된 메모리를 자동 생성합니다.

#### Endpoint
```
POST /v1/sessions/{session_id}/close
```

#### Request Body
```json
{
  "compression": "medium",
  "save_to_storage": true
}
```

#### Response
```json
{
  "success": true,
  "session_id": "sess_abc123",
  "status": "closed",
  "compressed_memory": "# 세션 메모리 (압축)\n...",
  "storage": {"saved": true, "storage_id": "mem-abc123"}
}
```

#### 권장 워크플로우
```
1. POST /v1/sessions (컨텍스트 주입)
2. POST /v1/chat/completions (대화 반복, 필요시 model 변경)
3. POST /v1/sessions/{id}/close (종료 + 메모리 저장)
4. POST /v1/sessions (새 세션 + previous_summary 주입)
```

## SSE Streaming (REST API)

스트리밍 응답을 위한 Server-Sent Events 형식입니다.

### Endpoint
```
POST /v1/chat/completions
Content-Type: application/json

{
  "messages": [...],
  "stream": true
}
```

### Response Headers
```
Content-Type: text/event-stream
Cache-Control: no-cache
Connection: keep-alive
X-Accel-Buffering: no
```

### Event Format
```
event: message
data: {"type": "content", "text": "Hello"}

event: message
data: {"type": "content", "text": " world!"}

event: done
data: {"type": "done", "usage": {"input_tokens": 10, "output_tokens": 25}}
```

### Event Types
| Event | Type | 설명 |
|-------|------|------|
| `message` | `content` | 텍스트 청크 |
| `message` | `thinking` | 사고 과정 (Claude only) |
| `error` | `error` | 에러 발생 |
| `done` | `done` | 스트리밍 완료 |

### 클라이언트 예시 (JavaScript)
```javascript
const response = await fetch('/v1/chat/completions', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-Session-ID': sessionId
  },
  body: JSON.stringify({
    messages: [{role: 'user', content: 'Hello'}],
    stream: true
  })
});

const reader = response.body.getReader();
const decoder = new TextDecoder();

while (true) {
  const {done, value} = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = JSON.parse(line.slice(6));
      if (data.type === 'content') {
        console.log(data.text);  // 실시간 출력
      }
    }
  }
}
```

### FastAPI 구현 예시
```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from typing import AsyncIterator
import json

async def stream_chat(prompt: str, provider: str) -> AsyncIterator[str]:
    """SSE 형식으로 스트리밍"""
    adapter = get_adapter(provider)

    async for chunk in adapter.chat_stream(prompt):
        event = {"type": "content", "text": chunk}
        yield f"event: message\ndata: {json.dumps(event)}\n\n"

    yield f"event: done\ndata: {json.dumps({'type': 'done'})}\n\n"

@app.post("/v1/chat/completions")
async def chat_completions(request: ChatRequest):
    if request.stream:
        return StreamingResponse(
            stream_chat(request.messages[-1].content, request.provider),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    # ... non-streaming response
```

## Error Handling

### 에러 코드
| 코드 | HTTP Status | 설명 |
|------|-------------|------|
| `PROVIDER_MISMATCH` | 400 | 세션의 provider와 다른 provider 요청 |
| `INVALID_MODEL` | 400 | 해당 provider가 지원하지 않는 모델 |
| `SESSION_NOT_FOUND` | 404 | 세션 ID가 존재하지 않음 |
| `SESSION_EXPIRED` | 410 | 세션 TTL 만료 |
| `PROVIDER_ERROR` | 502 | LLM Provider 호출 실패 |
| `PROVIDER_TIMEOUT` | 504 | LLM Provider 응답 타임아웃 |
| `TOKEN_EXPIRED` | 401 | OAuth 토큰 만료 |

### 에러 응답 형식
```json
{
  "error": {
    "code": "PROVIDER_MISMATCH",
    "message": "Session uses 'gemini' provider, cannot use 'claude'",
    "details": {
      "session_provider": "gemini",
      "requested_provider": "claude"
    }
  }
}
```

## Health Check

### 기본 헬스체크
```
GET /health
```

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 상세 헬스체크
```
GET /health/detailed
```

```json
{
  "status": "degraded",
  "version": "1.0.0",
  "components": {
    "redis": {
      "status": "healthy",
      "latency_ms": 2
    },
    "claude": {
      "status": "healthy",
      "last_success": "2024-01-01T00:00:00Z",
      "supported_models": ["claude-sonnet-4-5-20250929", "claude-opus-4-5-20251101", "claude-haiku-4-5-20251001"]
    },
    "gemini": {
      "status": "unhealthy",
      "error": "OAuth token expired",
      "supported_models": ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-2.0-flash"]
    }
  }
}
```

### 토큰 상태 확인
```
GET /health/tokens
```

```json
{
  "claude": {
    "valid": true,
    "expires_at": "2024-01-15T00:00:00Z",
    "days_remaining": 14
  },
  "gemini": {
    "valid": false,
    "error": "Token expired",
    "expired_at": "2024-01-01T00:00:00Z"
  }
}
```

## MCP Tools
- `create_session` - 세션 생성 (컨텍스트 주입)
- `chat` - LLM에 대화 요청
- `list_providers` - Provider 목록 조회
- `get_provider_models` - **Provider별 지원 모델 조회**
- `get_session` - 세션 정보 조회
- `export_session_memory` - 세션 메모리 내보내기 (압축 레벨 지원)
- `close_session` - 세션 종료 및 메모리 저장

## MCP Resources
- `provider://list` - Provider 목록
- `provider://{name}` - 특정 Provider 상세 정보
- `provider://{name}/models` - **Provider별 지원 모델 목록**
- `session://{session_id}` - 세션 정보 및 대화 기록

## Project Structure
```
llm-mcp-hub/
├── src/llm_mcp_hub/
│   ├── main.py              # FastAPI 앱 진입점
│   ├── core/                # 설정 및 공통 모듈
│   │   ├── config.py        # Pydantic Settings
│   │   ├── exceptions.py    # 커스텀 예외
│   │   ├── secrets.py       # 시크릿 로더
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
│   │       ├── claude.py    # Claude CLI Adapter
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
├── tests/
├── docker-compose.yml
└── Dockerfile
```

## Design Principles
1. **계층 분리**: API → Services → Domain → Infrastructure
2. **의존성 역전**: Infrastructure는 인터페이스에 의존
3. **API 버전 관리**: `/api/v1/`, `/api/v2/` 확장 가능
4. **모듈화**: 새 Provider 추가 시 파일만 추가
5. **테스트 용이성**: 인메모리 구현체로 테스트 가능

## Development Phases
1. **Phase 1: Foundation** - 프로젝트 설정, FastAPI, Redis, Claude CLI 연동
2. **Phase 2: Provider Integration** - Gemini PTY Adapter, REST API
3. **Phase 3: MCP Server** - MCP 서버, Tools, Resources, stdio/SSE
4. **Phase 4: Production Ready** - 에러 핸들링, 로깅, 테스트, 문서화

## Docker Deployment

### docker-compose.yml
```yaml
version: "3.8"

services:
  llm-mcp-hub:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
      - SESSION_TTL=3600
    secrets:
      - claude_oauth_token
      - gemini_oauth_creds
    volumes:
      # Gemini OAuth credentials (읽기 전용)
      - type: bind
        source: ./secrets/gemini
        target: /mnt/auth/gemini
        read_only: true
    depends_on:
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

secrets:
  claude_oauth_token:
    file: ./secrets/claude_oauth_token.txt
  gemini_oauth_creds:
    file: ./secrets/gemini/oauth_creds.json

volumes:
  redis_data:
```

### Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Node.js for claude-code CLI
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && npm install -g @anthropic/claude-code

# Install uv
RUN pip install uv

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install Python dependencies
RUN uv sync --frozen --no-dev

# Copy application code
COPY src/ ./src/

# Non-root user for security
RUN useradd -m -u 1000 appuser
USER appuser

# Environment variables
ENV PYTHONPATH=/app/src
ENV PYTHONUNBUFFERED=1

# Secrets paths (Docker Secrets mount point)
ENV CLAUDE_CODE_OAUTH_TOKEN_FILE=/run/secrets/claude_oauth_token
ENV GEMINI_AUTH_PATH=/mnt/auth/gemini/oauth_creds.json

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "llm_mcp_hub.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 시크릿 디렉토리 구조
```
secrets/
├── claude_oauth_token.txt    # Claude OAuth 토큰 (plain text)
└── gemini/
    └── oauth_creds.json      # Gemini OAuth credentials (JSON)
```

### 로컬 개발 환경
```bash
# .env 파일 (gitignore에 추가!)
CLAUDE_CODE_OAUTH_TOKEN=your-oauth-token-here
GEMINI_AUTH_PATH=./secrets/gemini/oauth_creds.json
REDIS_URL=redis://localhost:6379
LOG_LEVEL=DEBUG
```

### 배포 명령어
```bash
# 빌드 및 실행
docker-compose up -d --build

# 로그 확인
docker-compose logs -f llm-mcp-hub

# 헬스체크
curl http://localhost:8000/health
curl http://localhost:8000/health/tokens

# 종료
docker-compose down
```

## Success Metrics
- API 응답 시간: < 100ms (LLM 응답 제외)
- 가용성: 99.9%
- 지원 LLM: 2개 이상 (Claude, Gemini)
- MCP 클라이언트: Claude Desktop, Cursor 연동
- 세션 유지: 1시간 TTL
- 토큰 갱신 주기: 1~2주 (알림 자동화)
