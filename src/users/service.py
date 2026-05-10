from src.core.exceptions import ConflictError, NotFoundError
from src.users.repository import UserRepository
from src.users.schemas import UserCreate, UserList, UserRead, UserUpdate


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    async def create_user(self, data: UserCreate) -> UserRead:
        existing_user = await self.repository.get_by_tg_id(data.tg_id)
        if existing_user is not None:
            raise ConflictError("User with this Telegram id already exists")

        user = await self.repository.add(**data.model_dump())
        await self.repository.commit()
        return UserRead.model_validate(user)

    async def get_user(self, user_id: int) -> UserRead:
        user = await self.repository.get(user_id)
        if user is None:
            raise NotFoundError("User not found")
        return UserRead.model_validate(user)

    async def get_user_by_tg_id(self, tg_id: int) -> UserRead:
        user = await self.repository.get_by_tg_id(tg_id)
        if user is None:
            raise NotFoundError("User not found")
        return UserRead.model_validate(user)

    async def get_or_create_by_tg_id(self, tg_id: int, username: str | None) -> UserRead:
        user = await self.repository.get_by_tg_id(tg_id)
        if user is None:
            user = await self.repository.add(tg_id=tg_id, username=username)
            await self.repository.commit()
            return UserRead.model_validate(user)

        if username and user.username != username:
            user = await self.repository.update(user, username=username)
            await self.repository.commit()

        return UserRead.model_validate(user)

    async def list_users(self, *, offset: int = 0, limit: int = 100) -> UserList:
        users = await self.repository.list(offset=offset, limit=limit)
        total = await self.repository.count()
        return UserList(items=[UserRead.model_validate(user) for user in users], total=total)

    async def update_user(self, user_id: int, data: UserUpdate) -> UserRead:
        user = await self.repository.get(user_id)
        if user is None:
            raise NotFoundError("User not found")

        update_data = data.model_dump(exclude_unset=True)
        if update_data:
            user = await self.repository.update(user, **update_data)
            await self.repository.commit()

        return UserRead.model_validate(user)

    async def delete_user(self, user_id: int) -> None:
        user = await self.repository.get(user_id)
        if user is None:
            raise NotFoundError("User not found")
        await self.repository.delete(user)
        await self.repository.commit()
