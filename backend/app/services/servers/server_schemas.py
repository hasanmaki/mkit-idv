# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
"""Server schemas for repository CRUD operations."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ServerCreate(BaseModel):
    """Schema for creating a server record."""

    name: str
    base_url: str
    timeout: int
    retries: int
    wait_between_retries: int
    max_requests_queued: int
    is_active: bool = True
    is_used: bool = False
    parameters: dict[str, Any] | None = None
    notes: str | None = None


class ServerUpdate(BaseModel):
    """Schema for updating a server record."""

    name: str | None = None
    base_url: str | None = None
    timeout: int | None = None
    retries: int | None = None
    wait_between_retries: int | None = None
    max_requests_queued: int | None = None
    is_active: bool | None = None
    is_used: bool | None = None
    parameters: dict[str, Any] | None = None
    notes: str | None = None
