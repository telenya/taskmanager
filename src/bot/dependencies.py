from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from src.core.database import async_session_maker
from src.tasks.repository import TaskRepository
from src.tasks.service import TaskService
from src.users.repository import UserRepository
from src.users.service import UserService


@asynccontextmanager
async def user_service_context() -> AsyncIterator[UserService]:
    async with async_session_maker() as session:
        try:
            yield UserService(UserRepository(session))
        except Exception:
            await session.rollback()
            raise


@asynccontextmanager
async def task_service_context() -> AsyncIterator[TaskService]:
    async with async_session_maker() as session:
        try:
            user_repository = UserRepository(session)
            yield TaskService(TaskRepository(session), user_repository)
        except Exception:
            await session.rollback()
            raise
