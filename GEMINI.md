# Gemini Project Context: LLM MCP Hub

This document provides a synthesized overview of the LLM MCP Hub project for the Gemini agent. It is based on the detailed Product Requirements Document (PRD).

## 1. Core Project Goal

The primary objective is to create a central hub that provides a unified interface to multiple Large Language Models (LLMs) like Claude and Gemini. This hub will expose both a **REST API** (for services like n8n) and a **Model Context Protocol (MCP) Server** (for clients like Claude Desktop or Cursor).

The main business driver is **cost reduction**. The system is designed to leverage existing user subscriptions (e.g., Claude Pro/Max, Gemini Advanced) by using **SDK/CLI-based OAuth authentication**, avoiding the per-call costs associated with standard API keys.

## 2. Critical Constraint: No API Keys

**This is the most important rule for the project.**

-   **Forbidden:** Direct use of LLM provider API keys (e.g., Anthropic API Key, Google AI API Key) is strictly prohibited.
-   **Required Methods:**
    -   **Claude:** Use `claude-agent-sdk` with OAuth token (`CLAUDE_CODE_OAUTH_TOKEN` environment variable)
    -   **Gemini:** Use `ptyprocess` + Gemini CLI with OAuth token (file mount)

## 3. High-Level Architecture & Tech Stack

The system follows a clean, layered architecture.

### Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        LLM MCP Hub                               │
├─────────────────────────────────────────────────────────────────┤
│  Presentation Layer                                              │
│  ┌──────────────────────┐  ┌──────────────────────────────────┐ │
│  │ REST API (FastAPI)   │  │ MCP Server (stdio/SSE)           │ │
│  └──────────────────────┘  └──────────────────────────────────┘ │
├─────────────────────────────────────────────────────────────────┤
│  Service Layer (ChatService, SessionService)                    │
├─────────────────────────────────────────────────────────────────┤
│  Infrastructure Layer                                            │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐ │
│  │ Claude Adapter │  │ Gemini Adapter │  │ Session Store      │ │
│  │ (Agent SDK)    │  │ (PTY + CLI)    │  │ (Redis)            │ │
│  └────────────────┘  └────────────────┘  └────────────────────┘ │
└─────────────────────────────────────────────────────────────────┘
```

### Key Principles

-   Separation of Concerns (Presentation → Service → Domain → Infrastructure)
-   Dependency Inversion (Infrastructure components are interchangeable)
-   Modularity (e.g., adding a new LLM provider is straightforward)

### Technology Stack

| Area | Technology | Reason |
|------|------------|--------|
| Language | Python 3.11+ | asyncio, type hints |
| Framework | FastAPI | Async, OpenAPI auto-generation |
| **Claude Provider** | **claude-agent-sdk** | Official SDK, OAuth support, no TTY needed |
| **Gemini Provider** | **ptyprocess + CLI** | PTY wrapper for CLI control |
| MCP Server | mcp (Python SDK) | Official MCP SDK |
| Session Store | Redis | Distributed, TTL-based expiration |
| Package Manager | uv | Fast dependency installation |

## 4. Provider Implementation

### Claude Provider (Agent SDK)

```python
from claude_agent_sdk import query

async def chat(prompt: str) -> str:
    result = []
    async for message in query(prompt=prompt):
        result.append(str(message))
    return "".join(result)
```

**Environment Variable:**
```bash
CLAUDE_CODE_OAUTH_TOKEN=your-oauth-token
```

### Gemini Provider (PTY Wrapper)

Gemini CLI requires TTY, so we use `ptyprocess` to create a pseudo-terminal:

```python
from ptyprocess import PtyProcess

async def chat(prompt: str) -> str:
    proc = PtyProcess.spawn(["gemini", "-p", prompt])
    output = ""
    while proc.isalive():
        try:
            output += proc.read(1024).decode()
        except EOFError:
            break
    return output
```

**Token File Mount:**
```bash
# Mount ~/.gemini/oauth_creds.json to container
docker run -v ~/.gemini:/root/.gemini:ro llm-mcp-hub
```

## 5. Scope of Work

The project is divided into several key functional areas:

-   **Provider Management:** Implementing Claude Agent SDK adapter and Gemini PTY adapter
-   **API Gateway:** Building REST endpoints (e.g., `/v1/chat/completions`, `/v1/sessions/...`)
-   **MCP Server:** Implementing MCP tools (`chat`, `list_providers`) and resources
-   **Session Management:** Handling stateful conversations via `X-Session-ID` and Redis. This includes advanced features like injecting context at session creation (e.g., system prompts, files) and exporting session history/summaries to maintain context across long-running interactions.
-   **Token Management:** OAuth token health check and expiration alerts

## 6. OAuth Token Management

| Provider | Token Source | Container Setup | Refresh Cycle |
|----------|--------------|-----------------|---------------|
| Claude | `claude setup-token` | Environment variable | 1-2 weeks |
| Gemini | `gemini` (Google login) | File mount | 2-4 weeks |

## 7. Key Documents

-   **Full Product Requirements:** [docs/PRD.md](docs/PRD.md)
-   **API Specification:** [docs/API.md](docs/API.md)
-   **Token Generation Guide:** [docs/토큰생성방법.md](docs/토큰생성방법.md)
-   **Azure Deployment Guide:** [docs/azure-cloud-container.md](docs/azure-cloud-container.md)
