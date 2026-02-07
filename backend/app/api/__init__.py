from app.api.v1.health import router as health_router


def include_api_routers(app):
    """Include all API routers into the main application.

    Args:
        app: The FastAPI application instance.
    """
    app.include_router(health_router, prefix="/api/v1")
