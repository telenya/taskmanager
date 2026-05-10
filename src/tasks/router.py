from fastapi import APIRouter, Query, status

from src.tasks.dependencies import TaskServiceDep
from src.tasks.enums import TaskStatus
from src.tasks.schemas import (
    TaskClose,
    TaskCreate,
    TaskList,
    TaskRead,
    TaskStatusChange,
    TaskUpdate,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(data: TaskCreate, service: TaskServiceDep) -> TaskRead:
    return await service.create_task(data)


@router.get("", response_model=TaskList)
async def list_tasks(
    service: TaskServiceDep,
    creator_id: int | None = Query(default=None, gt=0),
    task_status: TaskStatus | None = Query(default=None, alias="status"),
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> TaskList:
    return await service.list_tasks(
        creator_id=creator_id,
        status=task_status,
        offset=offset,
        limit=limit,
    )


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(task_id: int, service: TaskServiceDep) -> TaskRead:
    return await service.get_task(task_id)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task(task_id: int, data: TaskUpdate, service: TaskServiceDep) -> TaskRead:
    return await service.update_task(task_id, data)


@router.patch("/{task_id}/status", response_model=TaskRead)
async def change_task_status(
    task_id: int,
    data: TaskStatusChange,
    service: TaskServiceDep,
) -> TaskRead:
    return await service.change_task_status(task_id, data)


@router.post("/{task_id}/close", response_model=TaskRead)
async def close_task(task_id: int, data: TaskClose, service: TaskServiceDep) -> TaskRead:
    return await service.close_task(task_id, data.actor_user_id)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(task_id: int, service: TaskServiceDep) -> None:
    await service.delete_task(task_id)
