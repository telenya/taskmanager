from typing import Annotated

from fastapi import Depends

from src.core.dependencies import SessionDep
from src.users.repository import UserRepository
from src.users.service import UserService


def get_user_service(session: SessionDep) -> UserService:
    return UserService(UserRepository(session))


UserServiceDep = Annotated[UserService, Depends(get_user_service)]
