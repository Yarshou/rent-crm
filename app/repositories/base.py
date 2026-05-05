from collections.abc import Iterable
from typing import Any, Generic, TypeVar
from uuid import UUID

from db.base.models import Base
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

__all__ = ["BaseRepository"]

ModelT = TypeVar("ModelT", bound=Base)
DTOT = TypeVar("DTOT", bound=BaseModel)


class BaseRepository(Generic[ModelT, DTOT]):
    model: type[ModelT]
    dto: type[DTOT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _to_dto(self, instance: ModelT) -> DTOT:
        return self.dto.model_validate(instance)

    def _to_dtos(self, instances: Iterable[ModelT]) -> list[DTOT]:
        return [self._to_dto(instance) for instance in instances]

    async def get(self, entity_id: UUID) -> DTOT | None:
        instance = await self.session.get(self.model, entity_id)
        return self._to_dto(instance) if instance is not None else None

    async def get_for_update(self, entity_id: UUID) -> DTOT | None:
        result = await self.session.execute(
            select(self.model).where(self.model.id == entity_id).with_for_update(),
        )
        instance = result.scalar_one_or_none()
        return self._to_dto(instance) if instance is not None else None

    async def list(self, *, offset: int = 0, limit: int | None = None) -> list[DTOT]:
        statement = select(self.model).offset(offset)
        if limit is not None:
            statement = statement.limit(limit)

        result = await self.session.execute(statement)
        return self._to_dtos(result.scalars().all())

    async def create(self, **values: Any) -> DTOT:
        instance = self.model(**values)
        self.session.add(instance)
        await self.session.flush()
        return self._to_dto(instance)

    async def update(self, entity_id: UUID, **values: Any) -> DTOT | None:
        instance = await self.session.get(self.model, entity_id)
        if instance is None:
            return None
        for field, value in values.items():
            setattr(instance, field, value)
        await self.session.flush()
        return self._to_dto(instance)

    async def delete_by_id(self, entity_id: UUID) -> bool:
        result = await self.session.execute(delete(self.model).where(self.model.id == entity_id))
        return result.rowcount > 0

    async def flush(self) -> None:
        await self.session.flush()
