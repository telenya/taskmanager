import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.redis import RedisStorage

from src.bot.handlers import router
from src.core.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    if not settings.bot_enabled:
        logger.warning("BOT_TOKEN is not set. Telegram bot is running in disabled mode.")
        while True:
            await asyncio.sleep(3600)

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    storage = RedisStorage.from_url(settings.redis_url)
    dispatcher = Dispatcher(storage=storage)
    dispatcher.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    try:
        await dispatcher.start_polling(bot)
    finally:
        await storage.close()
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
