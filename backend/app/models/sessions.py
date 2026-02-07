# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
# [ ] TODO : Fix Later About Docstring
"""This Class Is for managing user sessions.

Note:
    - Important constraints or considerations
"""

import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import Base, TimestampMixin


class Session(Base, TimestampMixin):
    """Session model representing user sessions."""

    __tablename__ = "sessions"

    id: Mapped[int] = mapped_column(primary_key=True)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        index=True,
        nullable=False,
    )

    # Identitas session (dipakai di JWT jti)
    session_id: Mapped[str] = mapped_column(
        unique=True,
        index=True,
        nullable=False,
    )

    # Refresh token (hash, bukan plaintext)
    refresh_token_hash: Mapped[str] = mapped_column(
        unique=True,
        nullable=False,
    )

    # Status session
    is_revoked: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    revoked_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)

    # Lifetime & activity
    expires_at: Mapped[datetime.datetime] = mapped_column(nullable=False)
    last_activity_at: Mapped[datetime.datetime | None] = mapped_column(nullable=True)

    # Audit context
    ip_address: Mapped[str | None] = mapped_column(nullable=True)
    user_agent: Mapped[str | None] = mapped_column(nullable=True)

    def __repr__(self) -> str:
        """Return a string representation of the Session."""
        return f"<Session id={self.id} user_id={self.user_id} session_id={self.session_id}>"
