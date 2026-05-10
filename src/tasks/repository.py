from datetime import datetime

from sqlalchemy import Select, func, select
from sqlalchemy.orm import selectinload

from src.core.repository import SQLAlchemyRepository
from src.tasks.enums import TaskStatus
from src.tasks.models import Task


class TaskRepository(SQLAlchemyRepository[Task]):
    model = Task

    async def list_filtered(
        self,
        *,
        creator_id: int | None = None,
        status: TaskStatus | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        stmt = self._filtered_select(creator_id=creator_id, status=status)
        stmt = stmt.order_by(Task.deadline, Task.id).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        *,
        creator_id: int | None = None,
        status: TaskStatus | None = None,
    ) -> int:
        stmt = select(func.count()).select_from(Task)
        if creator_id is not None:
            stmt = stmt.where(Task.creator_id == creator_id)
        if status is not None:
            stmt = stmt.where(Task.status == status)
        result = await self.session.execute(stmt)
        return int(result.scalar_one())

    async def list_for_deadline_reminder(
        self,
        *,
        lower_bound: datetime,
        upper_bound: datetime,
    ) -> list[Task]:
        stmt = (
            select(Task)
            .options(selectinload(Task.creator))
            .where(
                Task.status != TaskStatus.DONE,
                Task.reminder_sent_at.is_(None),
                Task.deadline >= lower_bound,
                Task.deadline < upper_bound,
            )
            .order_by(Task.deadline, Task.id)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    def _filtered_select(
        self,
        *,
        creator_id: int | None,
        status: TaskStatus | None,
    ) -> Select[tuple[Task]]:
        stmt = select(Task)
        if creator_id is not None:
            stmt = stmt.where(Task.creator_id == creator_id)
        if status is not None:
            stmt = stmt.where(Task.status == status)
        return stmt
