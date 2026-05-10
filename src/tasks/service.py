from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

from src.core.config import get_settings
from src.core.exceptions import ForbiddenError, NotFoundError
from src.tasks.enums import TaskStatus
from src.tasks.repository import TaskRepository
from src.tasks.schemas import (
    TaskCreate,
    TaskList,
    TaskRead,
    TaskReminderRead,
    TaskStatusChange,
    TaskUpdate,
)
from src.users.repository import UserRepository


class TaskService:
    def __init__(self, task_repository: TaskRepository, user_repository: UserRepository) -> None:
        self.task_repository = task_repository
        self.user_repository = user_repository
        self.settings = get_settings()

    async def create_task(self, data: TaskCreate) -> TaskRead:
        creator = await self.user_repository.get(data.creator_id)
        if creator is None:
            raise NotFoundError("Task creator not found")

        task_data = data.model_dump()
        task_data["deadline"] = self._ensure_aware_datetime(data.deadline)
        task = await self.task_repository.add(**task_data)
        await self.task_repository.commit()
        return TaskRead.model_validate(task)

    async def get_task(self, task_id: int) -> TaskRead:
        task = await self.task_repository.get(task_id)
        if task is None:
            raise NotFoundError("Task not found")
        return TaskRead.model_validate(task)

    async def list_tasks(
        self,
        *,
        creator_id: int | None = None,
        status: TaskStatus | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> TaskList:
        tasks = await self.task_repository.list_filtered(
            creator_id=creator_id,
            status=status,
            offset=offset,
            limit=limit,
        )
        total = await self.task_repository.count_filtered(creator_id=creator_id, status=status)
        return TaskList(items=[TaskRead.model_validate(task) for task in tasks], total=total)

    async def list_tasks_by_tg_id(self, tg_id: int) -> TaskList:
        user = await self.user_repository.get_by_tg_id(tg_id)
        if user is None:
            raise NotFoundError("User not found")
        return await self.list_tasks(creator_id=user.id)

    async def update_task(self, task_id: int, data: TaskUpdate) -> TaskRead:
        task = await self.task_repository.get(task_id)
        if task is None:
            raise NotFoundError("Task not found")

        update_data = data.model_dump(exclude_unset=True)
        if update_data.get("title") is None:
            update_data.pop("title", None)
        if update_data.get("deadline") is None:
            update_data.pop("deadline", None)
        if "deadline" in update_data and update_data["deadline"] is not None:
            update_data["deadline"] = self._ensure_aware_datetime(update_data["deadline"])

        if update_data:
            task = await self.task_repository.update(task, **update_data)
            await self.task_repository.commit()

        return TaskRead.model_validate(task)

    async def change_task_status(self, task_id: int, data: TaskStatusChange) -> TaskRead:
        task = await self.task_repository.get(task_id)
        if task is None:
            raise NotFoundError("Task not found")

        actor = await self.user_repository.get(data.actor_user_id)
        if actor is None:
            raise NotFoundError("Actor user not found")
        if task.creator_id != actor.id:
            raise ForbiddenError("Only the creator can change task status")

        task = await self.task_repository.update(task, status=data.status)
        await self.task_repository.commit()
        return TaskRead.model_validate(task)

    async def close_task(self, task_id: int, actor_user_id: int) -> TaskRead:
        return await self.change_task_status(
            task_id,
            TaskStatusChange(actor_user_id=actor_user_id, status=TaskStatus.DONE),
        )

    async def delete_task(self, task_id: int) -> None:
        task = await self.task_repository.get(task_id)
        if task is None:
            raise NotFoundError("Task not found")
        await self.task_repository.delete(task)
        await self.task_repository.commit()

    async def list_deadline_reminders(
        self,
        *,
        reference_time: datetime | None = None,
    ) -> list[TaskReminderRead]:
        now = reference_time or datetime.now(UTC)
        lower_bound = now + timedelta(minutes=59)
        upper_bound = now + timedelta(minutes=61)
        tasks = await self.task_repository.list_for_deadline_reminder(
            lower_bound=lower_bound,
            upper_bound=upper_bound,
        )
        return [
            TaskReminderRead(
                id=task.id,
                title=task.title,
                deadline=task.deadline,
                creator_id=task.creator_id,
                creator_tg_id=task.creator.tg_id,
                creator_username=task.creator.username,
            )
            for task in tasks
        ]

    async def mark_reminder_sent(self, task_id: int, *, sent_at: datetime | None = None) -> None:
        task = await self.task_repository.get(task_id)
        if task is None:
            raise NotFoundError("Task not found")
        await self.task_repository.update(task, reminder_sent_at=sent_at or datetime.now(UTC))
        await self.task_repository.commit()

    def _ensure_aware_datetime(self, value: datetime) -> datetime:
        if value.tzinfo is not None:
            return value
        return value.replace(tzinfo=ZoneInfo(self.settings.timezone))
