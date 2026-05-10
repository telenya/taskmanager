from typing import Any, Generic, TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

ModelT = TypeVar("ModelT")


class SQLAlchemyRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get(self, obj_id: Any) -> ModelT | None:
        return await self.session.get(self.model, obj_id)

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[ModelT]:
        stmt = self._base_select().offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self) -> int:
        stmt = select(func.count()).select_from(self.model)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def add(self, **data: Any) -> ModelT:
        obj = self.model(**data)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: ModelT, **data: Any) -> ModelT:
        for field, value in data.items():
            setattr(obj, field, value)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete(self, obj: ModelT) -> None:
        self.session.delete(obj)
        await self.session.flush()

    async def commit(self) -> None:
        await self.session.commit()

    async def rollback(self) -> None:
        await self.session.rollback()

    def _base_select(self) -> Select[tuple[ModelT]]:
        return select(self.model)
