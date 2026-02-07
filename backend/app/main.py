from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.utils.httpx_factory import create_async_client
from loguru import logger

from app.api import include_api_routers
from app.core import configure_logging
from app.core.exceptions import register_exception_handlers
from app.core.middleware.logging import RequestLoggingMiddleware
from app.core.settings import get_app_settings

settings = get_app_settings()


@asynccontextmanager
async def lifespan_app(app: FastAPI):  # noqa: ARG001, RUF029
    """Lifespan context manager for FastAPI application.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    logger.info("Starting application lifespan...")
    app.state.httpx = create_async_client(settings.httpx)
    yield
    await app.state.httpx.aclose()
    logger.info("Ending application lifespan...")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    configure_logging()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan_app,
    )

    app.add_middleware(RequestLoggingMiddleware)

    # CORS configuration
    app.add_middleware(
        middleware_class=CORSMiddleware,
        allow_origins=settings.cors.allow_origins,
        allow_methods=settings.cors.allow_methods,
        allow_headers=settings.cors.allow_headers,
        allow_credentials=settings.cors.allow_credentials,
    )

    # Register exception handlers
    register_exception_handlers(app)

    # Include API routers
    include_api_routers(app)

    return app


app = create_app()
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_config=None,
        access_log=False,
    )
