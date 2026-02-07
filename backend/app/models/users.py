# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
# [ ] TODO : Fix Later About Docstring
"""uSERS ORM MODELS.

User adalah Penguna Aplikasi

Note:
    - This module contains the ORM models for the User entity.
"""

from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import Base, TimestampMixin


class User(Base, TimestampMixin):
    """User model representing application users."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(nullable=False)
    username: Mapped[str] = mapped_column(unique=True, nullable=False)
    email: Mapped[str] = mapped_column(unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(nullable=False)
    is_admin: Mapped[bool] = mapped_column(default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    def __repr__(self) -> str:
        """Return a string representation of the User."""
        return f"<User id={self.id} username={self.username} email={self.email}>"
