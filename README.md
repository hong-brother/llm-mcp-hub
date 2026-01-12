# LLM MCP Hub

Multi-LLM Hub API with MCP Server - Claude, Gemini 통합 API 제공

## Overview

기존 Claude Pro/Max, Gemini Advanced 구독을 활용하여 REST API 및 MCP 서버로 제공하는 허브 시스템입니다.

> **API Key 사용 금지** - OAuth 토큰 기반 인증으로 구독 플랜 활용

| Provider | 방식 | 인증 |
|----------|------|------|
| Claude | Agent SDK | `CLAUDE_CODE_OAUTH_TOKEN` 환경변수 |
| Gemini | CLI + PTY Wrapper | OAuth 파일 마운트 |

## Requirements

- Docker & Docker Compose
- Claude Code CLI 인증 완료 (`claude login`)
- Gemini CLI 인증 완료 (`gemini`)

## Quick Start

### 1. OAuth 토큰 준비

**Claude 토큰 설정:**
```bash
# Claude Code CLI로 로그인 후 토큰 확인
claude login

# 환경변수 설정
export CLAUDE_CODE_OAUTH_TOKEN="your-oauth-token"

# 또는 .env 파일에 저장
echo "CLAUDE_CODE_OAUTH_TOKEN=your-oauth-token" >> .env
```

**Gemini 인증:**
```bash
# Gemini CLI 실행하여 브라우저 인증
gemini

# ~/.gemini/oauth_creds.json 파일이 생성됨
```

### 2. Docker Compose 실행

```bash
# 빌드 및 테스트 실행
docker compose up --build

# 백그라운드 실행
docker compose up -d --build

# 로그 확인
docker compose logs -f

# 종료
docker compose down
```

### 3. 테스트만 실행

```bash
# POC 테스트 실행 (Claude SDK + Gemini PTY)
docker compose run --rm poc-test
```

## Local Development

```bash
# uv 설치
pip install uv

# 의존성 설치
uv sync

# 가상환경 활성화
source .venv/bin/activate

# 테스트 실행
python tests/poc/test_claude_sdk.py
python tests/poc/test_gemini_pty.py
```

## Project Structure

```
llm-mcp-hub/
├── src/llm_mcp_hub/      # 메인 소스 코드
├── tests/poc/            # POC 테스트
├── docs/                 # 문서
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## Documentation

- [PRD (요구사항 정의서)](docs/PRD.md)
- [API 명세서](docs/API.md)
- [토큰 생성 방법](docs/토큰생성방법.md)
- [Azure 배포 가이드](docs/azure-cloud-container.md)
