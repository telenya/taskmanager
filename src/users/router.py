from fastapi import APIRouter, Query, status

from src.users.dependencies import UserServiceDep
from src.users.schemas import UserCreate, UserList, UserRead, UserUpdate

router = APIRouter(prefix="/users", tags=["users"])


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def create_user(data: UserCreate, service: UserServiceDep) -> UserRead:
    return await service.create_user(data)


@router.get("", response_model=UserList)
async def list_users(
    service: UserServiceDep,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=100, ge=1, le=500),
) -> UserList:
    return await service.list_users(offset=offset, limit=limit)


@router.get("/by-tg/{tg_id}", response_model=UserRead)
async def get_user_by_tg_id(tg_id: int, service: UserServiceDep) -> UserRead:
    return await service.get_user_by_tg_id(tg_id)


@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, service: UserServiceDep) -> UserRead:
    return await service.get_user(user_id)


@router.patch("/{user_id}", response_model=UserRead)
async def update_user(user_id: int, data: UserUpdate, service: UserServiceDep) -> UserRead:
    return await service.update_user(user_id, data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user_id: int, service: UserServiceDep) -> None:
    await service.delete_user(user_id)
