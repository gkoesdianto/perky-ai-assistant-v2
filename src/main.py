import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from src.core.config import settings
from src.infrastructure.container import get_singleton_container
from src.infrastructure.observability import configure_logfire, setup_instrumentation
from src.presentation.api import health
from src.presentation.api.v1 import websocket

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info("Starting Steel Chat MVP application...")

    # Configure Logfire FIRST (before any other services)
    configure_logfire()

    # Initialize DI container
    get_singleton_container()
    logger.info("Services configured successfully")

    yield

    logger.info("Shutting down application...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application"""

    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    # Set up instrumentation (after app creation, before middleware)
    logfire_instance = configure_logfire()
    setup_instrumentation(app, logfire_instance)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["*"],
    )

    app.include_router(health.router, tags=["health"])
    app.include_router(websocket.router, prefix=settings.API_V1_STR, tags=["websocket"])

    @app.get("/", response_class=HTMLResponse)
    async def root():
        """Serve test client interface"""
        try:
            with open("static/test_client.html", "r") as f:
                return HTMLResponse(content=f.read())
        except FileNotFoundError:
            return HTMLResponse(
                content=(
                    "<h1>Steel Chat MVP</h1>"
                    "<p>WebSocket endpoint: /api/v1/ws/{session_id}</p>"
                )
            )

    @app.get("/api")
    async def api_redirect():
        """Redirect to API documentation"""
        return {"message": "API Documentation", "url": "/docs"}

    return app


app = create_app()

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "src.main:app",
        host="0.0.0.0",  # nosec B104 - Binding to all interfaces for development
        port=8000,
        reload=True,
        log_level="info",
    )
