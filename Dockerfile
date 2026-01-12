# LLM MCP Hub - POC Test Container
# Python 3.11 + Node.js (Gemini CLI용)

FROM python:3.11-slim

# 환경변수 설정
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# 시스템 의존성 설치
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Node.js 설치 (Gemini CLI용)
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && rm -rf /var/lib/apt/lists/*

# Gemini CLI 설치
RUN npm install -g @google/gemini-cli

# Claude Code CLI 설치 (SDK가 내부적으로 사용)
RUN npm install -g @anthropic-ai/claude-code

# uv 설치
RUN pip install uv

# 작업 디렉토리 설정
WORKDIR /app

# 프로젝트 파일 복사
COPY pyproject.toml README.md ./
COPY src/ ./src/
COPY tests/ ./tests/

# 의존성 설치
RUN uv pip install --system -e ".[dev]"

# 테스트 실행 스크립트
COPY <<'EOF' /app/run_tests.sh
#!/bin/bash
set -e

echo "========================================"
echo "LLM MCP Hub - POC 테스트"
echo "========================================"

echo ""
echo "[1/2] Claude SDK 테스트"
echo "----------------------------------------"
python tests/poc/test_claude_sdk.py

echo ""
echo "[2/2] Gemini PTY 테스트"
echo "----------------------------------------"
python tests/poc/test_gemini_pty.py

echo ""
echo "========================================"
echo "모든 테스트 완료"
echo "========================================"
EOF
RUN chmod +x /app/run_tests.sh

# 기본 명령어
CMD ["/app/run_tests.sh"]
