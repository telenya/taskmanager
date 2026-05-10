from sqlalchemy import select

from src.core.repository import SQLAlchemyRepository
from src.users.models import User


class UserRepository(SQLAlchemyRepository[User]):
    model = User

    async def get_by_tg_id(self, tg_id: int) -> User | None:
        stmt = select(User).where(User.tg_id == tg_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list(self, *, offset: int = 0, limit: int = 100) -> list[User]:
        stmt = select(User).order_by(User.id).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())
