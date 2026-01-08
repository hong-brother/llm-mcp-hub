# Gemini Project Context: LLM MCP Hub

This document provides a synthesized overview of the LLM MCP Hub project for the Gemini agent. It is based on the detailed Product Requirements Document (PRD).

## 1. Core Project Goal

The primary objective is to create a central hub that provides a unified interface to multiple Large Language Models (LLMs) like Claude and Gemini. This hub will expose both a **REST API** (for services like n8n) and a **Model Context Protocol (MCP) Server** (for clients like Claude Desktop or Cursor).

The main business driver is **cost reduction**. The system is designed to leverage existing user subscriptions (e.g., Claude Pro, Gemini Advanced) by using CLI-based authentication, avoiding the per-call costs associated with standard API keys.

## 2. Critical Constraint: No API Keys

**This is the most important rule for the project.**

-   **Forbidden:** Direct use of LLM provider API keys (e.g., Anthropic API Key, Google AI API Key) is strictly prohibited.
-   **Required Method:** The system must authenticate by driving the official CLI tools of the LLM providers via `subprocess`. This involves managing OAuth tokens obtained through the CLI flow within a Docker container.

## 3. High-Level Architecture & Tech Stack

The system follows a clean, layered architecture.

-   **Key Principles:**
    -   Separation of Concerns (Presentation → Service → Domain → Infrastructure)
    -   Dependency Inversion (Infrastructure components are interchangeable)
    -   Modularity (e.g., adding a new LLM provider is straightforward)

-   **Technology Stack:**
    -   **Language:** Python 3.11+
    -   **Framework:** FastAPI (for the REST API)
    -   **Asynchronous Execution:** `asyncio` for handling concurrent requests and managing subprocesses.
    -   **Session Management:** Redis (for storing conversation history and session state).
    -   **MCP Server:** `mcp` Python SDK.
    -   **Package Management:** `uv`.

## 4. Scope of Work

The project is divided into several key functional areas:

-   **Provider Management:** Implementing `subprocess`-based workers for Claude and Gemini.
-   **API Gateway:** Building REST endpoints (e.g., `/v1/chat/completions`, `/v1/sessions/...`).
-   **MCP Server:** Implementing MCP tools (`chat`, `list_providers`) and resources.
-   **Session Management:** Handling conversation context and state via `X-Session-ID` headers and Redis.
-   **Process Management:** Reliably managing the lifecycle of the LLM subprocesses.

## 5. Key Documents

-   **Full Product Requirements:** [docs/PRD.md](docs/PRD.md)