"""FastAPI application entry point"""
import logging
import re
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from llm_mcp_hub.core.config import get_settings
from llm_mcp_hub.core.exceptions import LLMHubError
from llm_mcp_hub.infrastructure.session import MemorySessionStore, RedisSessionStore
from llm_mcp_hub.infrastructure.providers import ClaudeAdapter, GeminiAdapter
from llm_mcp_hub.services import ChatService, SessionService, MemoryService
from llm_mcp_hub.api.v1 import router as api_v1_router
from llm_mcp_hub.api.v1.health import router as health_router

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class TokenMaskingFilter(logging.Filter):
    """Filter to mask sensitive tokens in logs"""

    PATTERNS = [
        (r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+", "[JWT_MASKED]"),
        (r'oauth_token["\']?\s*[:=]\s*["\']?[\w-]+', "oauth_token=[MASKED]"),
        (r"CLAUDE_CODE_OAUTH_TOKEN=\S+", "CLAUDE_CODE_OAUTH_TOKEN=[MASKED]"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            for pattern, replacement in self.PATTERNS:
                record.msg = re.sub(pattern, replacement, record.msg)
        return True


# Add token masking filter to root logger
logging.getLogger().addFilter(TokenMaskingFilter())


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - startup and shutdown"""
    settings = get_settings()

    logger.info("Starting LLM MCP Hub...")
    logger.info(f"Debug mode: {settings.debug}")
    logger.info(f"Log level: {settings.log_level}")

    # Initialize session store
    if settings.redis_url and not settings.debug:
        logger.info(f"Using Redis session store: {settings.redis_url}")
        session_store = RedisSessionStore(
            redis_url=settings.redis_url,
            ttl=settings.session_ttl,
        )
        try:
            await session_store.connect()
        except Exception as e:
            logger.warning(f"Redis connection failed, using memory store: {e}")
            session_store = MemorySessionStore(ttl=settings.session_ttl)
    else:
        logger.info("Using in-memory session store")
        session_store = MemorySessionStore(ttl=settings.session_ttl)

    # Initialize providers
    providers = {}

    # Claude provider
    if settings.claude_oauth_token:
        logger.info("Initializing Claude provider...")
        claude_adapter = ClaudeAdapter(
            oauth_token=settings.claude_oauth_token,
            default_model=settings.claude_default_model,
        )
        try:
            await claude_adapter.initialize()
            providers["claude"] = claude_adapter
            logger.info(f"Claude models: {claude_adapter.supported_models}")
        except Exception as e:
            logger.error(f"Claude initialization failed: {e}")
    else:
        logger.warning("Claude OAuth token not configured, provider disabled")

    # Gemini provider
    if settings.gemini_auth_path:
        logger.info("Initializing Gemini provider...")
        gemini_adapter = GeminiAdapter(
            auth_path=settings.gemini_auth_path,
            default_model=settings.gemini_default_model,
        )
        try:
            await gemini_adapter.initialize()
            providers["gemini"] = gemini_adapter
            logger.info(f"Gemini models: {gemini_adapter.supported_models}")
        except Exception as e:
            logger.error(f"Gemini initialization failed: {e}")
    else:
        logger.warning("Gemini auth path not configured, provider disabled")

    if not providers:
        logger.warning("No providers configured! API will return errors for chat requests.")

    # Initialize services
    session_service = SessionService(
        session_store=session_store,
        providers=providers,
        default_ttl=settings.session_ttl,
    )

    chat_service = ChatService(
        providers=providers,
        session_service=session_service,
    )

    memory_service = MemoryService(
        session_service=session_service,
        chat_service=chat_service,
    )

    # Store in app state for dependency injection
    app.state.settings = settings
    app.state.session_store = session_store
    app.state.providers = providers
    app.state.session_service = session_service
    app.state.chat_service = chat_service
    app.state.memory_service = memory_service

    logger.info("LLM MCP Hub started successfully")
    logger.info(f"Available providers: {list(providers.keys())}")

    yield

    # Shutdown
    logger.info("Shutting down LLM MCP Hub...")

    # Close session store
    await session_store.close()

    logger.info("LLM MCP Hub shutdown complete")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Multi-LLM Provider Hub with REST API and MCP Server",
        lifespan=lifespan,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(api_v1_router)
    app.include_router(health_router)

    # Global exception handler for LLMHubError
    @app.exception_handler(LLMHubError)
    async def llm_hub_error_handler(request: Request, exc: LLMHubError):
        status_map = {
            "PROVIDER_MISMATCH": 400,
            "INVALID_MODEL": 400,
            "SESSION_NOT_FOUND": 404,
            "SESSION_EXPIRED": 410,
            "PROVIDER_ERROR": 502,
            "PROVIDER_TIMEOUT": 504,
            "TOKEN_EXPIRED": 401,
        }
        status_code = status_map.get(exc.code, 500)
        return JSONResponse(
            status_code=status_code,
            content=exc.to_dict(),
        )

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
        }

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "llm_mcp_hub.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
