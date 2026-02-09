# Copyright (c) 2026 okedigitalmedia/hasanmaki. All rights reserved.
"""Base repository utilities for common CRUD behavior."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """Base repository with shared CRUD helpers."""

    def __init__(self, db: AsyncSession, model: type[ModelType], id_field: str = "id"):
        self.db = db
        self.model = model
        self.id_field = id_field

    async def get_by_id(self, obj_id: Any) -> ModelType | None:
        """Get entity by primary key-like field."""
        field = getattr(self.model, self.id_field)
        result = await self.db.execute(select(self.model).where(field == obj_id))
        return result.scalar_one_or_none()

    async def get_multi(self, skip: int = 0, limit: int = 100) -> Sequence[ModelType]:
        """List entities with pagination."""
        stmt = select(self.model).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def create(self, obj_in: CreateSchemaType | Mapping[str, Any]) -> ModelType:
        """Create a new entity from a schema or mapping."""
        if isinstance(obj_in, BaseModel):
            data = obj_in.model_dump(exclude_unset=True)
        else:
            data = dict(obj_in)
        db_obj = self.model(**data)
        self.db.add(db_obj)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def update(
        self,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | Mapping[str, Any],
    ) -> ModelType:
        """Update an entity from a schema or mapping."""
        if isinstance(obj_in, BaseModel):
            update_data = obj_in.model_dump(exclude_unset=True)
        else:
            update_data = dict(obj_in)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        await self.db.flush()
        await self.db.refresh(db_obj)
        return db_obj

    async def delete(self, obj_id: Any) -> bool:
        """Delete an entity by id."""
        obj = await self.get_by_id(obj_id)
        if not obj:
            return False
        await self.db.delete(obj)
        await self.db.flush()
        return True

    async def add(self, obj: ModelType) -> None:
        """Add and flush a new entity."""
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)

    async def save(self) -> None:
        """Flush pending changes to the database."""
        await self.db.flush()
