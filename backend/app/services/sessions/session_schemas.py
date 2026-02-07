# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
# [ ] TODO : Fix Later About Docstring
"""Module Title.

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

from datetime import datetime

from pydantic import BaseModel


class SessionCreate(BaseModel):
    """Schema for creating a new session."""

    user_id: int
    session_id: str
    refresh_token_hash: str
    expires_at: datetime
    ip_address: str | None = None
    user_agent: str | None = None

    model_config = {
        "from_attributes": True,
    }


class SessionValidationResult(BaseModel):
    """Schema for session validation result."""

    user_id: int
    session_id: str

    model_config = {
        "from_attributes": True,
    }


class SessionPublic(BaseModel):
    """Public schema for session data."""

    session_id: str
    is_revoked: bool
    expires_at: datetime
    last_activity_at: datetime | None
    ip_address: str | None
    user_agent: str | None

    model_config = {
        "from_attributes": True,
    }
