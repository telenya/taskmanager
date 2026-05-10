from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from src.core.config import get_settings


@asynccontextmanager
async def worker_session_context() -> AsyncIterator[AsyncSession]:
    settings = get_settings()
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        pool_pre_ping=True,
    )
    session_maker = async_sessionmaker(
        bind=engine,
        expire_on_commit=False,
        autoflush=False,
    )

    try:
        async with session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
    finally:
        await engine.dispose()
