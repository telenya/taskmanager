from typing import Annotated

from fastapi import Depends

from src.core.dependencies import SessionDep
from src.tasks.repository import TaskRepository
from src.tasks.service import TaskService
from src.users.repository import UserRepository


def get_task_service(session: SessionDep) -> TaskService:
    return TaskService(TaskRepository(session), UserRepository(session))


TaskServiceDep = Annotated[TaskService, Depends(get_task_service)]
