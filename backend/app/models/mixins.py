# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
# [ ] TODO : Fix Later About Docstring
"""This Module Provide a Mixins, for commong fields.

    SQL Alchemy Mixins

Note:
    - Important constraints or considerations
"""

from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class TimestampMixin:
    """Mixin to add created_at and updated_at to models."""

    created_at: Mapped[datetime] = mapped_column(default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        default=func.now(), onupdate=func.now(), nullable=False
    )


class Base(DeclarativeBase):
    """Base class for SQL Alchemy models."""

    pass
