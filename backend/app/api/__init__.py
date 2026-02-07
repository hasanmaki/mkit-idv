def include_api_routers(app):
    """Include all API routers into the main application.

    Args:
        app: The FastAPI application instance.
    """
    from app.api.v1.auth import router as auth_router
    from app.api.v1.health import router as health_router

    app.include_router(health_router, prefix="/api/v1")
    app.include_router(auth_router, prefix="/api/v1")
