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

from typing import Any

from sqlalchemy import JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.mixins import Base, TimestampMixin


class Servers(Base, TimestampMixin):
    """Servers Model.

    This class represents an API server in the system.

    Attributes:
        id (int): The unique identifier for the API server.
        name (str): The name of the API server.
        base_url (str): The base URL of the API server.
    """

    __tablename__ = "servers"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    base_url: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    timeout: Mapped[int] = mapped_column(nullable=False)
    retries: Mapped[int] = mapped_column(nullable=False)
    wait_between_retries: Mapped[int] = mapped_column(nullable=False)
    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
    )
    is_used: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    max_requests_queued: Mapped[int] = mapped_column(nullable=False)
    parameters: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)
    notes: Mapped[str] = mapped_column(String(255), nullable=True)

    def __repr__(self) -> str:
        """Return a string representation of the Servers."""
        return f"<Servers id={self.id} name={self.name} base_url={self.base_url}>"
