from typing import Any, Generic, TypeVar
from uuid import UUID

from db.base.models import Base
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["BaseRepository"]

ModelT = TypeVar("ModelT", bound=Base)


class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, entity_id: UUID) -> ModelT | None:
        return await self.session.get(self.model, entity_id)

    async def get_for_update(self, entity_id: UUID) -> ModelT | None:
        result = await self.session.execute(
            select(self.model).where(self.model.id == entity_id).with_for_update(),
        )
        return result.scalar_one_or_none()

    async def list(self, *, offset: int = 0, limit: int | None = None) -> list[ModelT]:
        statement = select(self.model).offset(offset)
        if limit is not None:
            statement = statement.limit(limit)

        result = await self.session.execute(statement)
        return list(result.scalars().all())

    async def add(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        return instance

    async def create(self, **values: Any) -> ModelT:
        instance = self.model(**values)
        self.session.add(instance)
        return instance

    async def update(self, instance: ModelT, **values: Any) -> ModelT:
        for field, value in values.items():
            setattr(instance, field, value)
        return instance

    async def delete(self, instance: ModelT) -> None:
        await self.session.delete(instance)

    async def delete_by_id(self, entity_id: UUID) -> bool:
        result = await self.session.execute(delete(self.model).where(self.model.id == entity_id))
        return result.rowcount > 0

    async def flush(self) -> None:
        await self.session.flush()

    async def refresh(self, instance: ModelT) -> None:
        await self.session.refresh(instance)
