# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
# [ ] TODO : Fix Later About Docstring
"""Simple Health Check.

Short description of this module and its responsibilities. Explain its purpose within the application architecture.

Key Features:
    - First key feature
    - Second key feature

Attributes:
    - Second key feature
    - Second key feature

Example:
    from module import something

Note:
    - Important constraints or considerations
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from app.core.exceptions.base import AppNotFoundError

router = APIRouter()


@router.get(
    "/health",
    response_class=JSONResponse,
    status_code=status.HTTP_200_OK,
    summary="Health Check Endpoint",
    tags=["Health"],
)
async def health_check():
    """Health check endpoint to verify that the application is running.

    Returns:
        JSONResponse: A JSON response indicating the health status.
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "healthy", "message": "Application is running smoothly."},
    )


# testing exceptions
@router.get("/health/error", tags=["Health"])
async def health_check_error():
    """Endpoint to simulate an error for testing exception handling.

    Raises:
        Exception: A generic exception to test error handling.
    """
    raise AppNotFoundError("Simulated not found error for testing purposes.")
