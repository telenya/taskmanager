import asyncio
import logging
from html import escape
from zoneinfo import ZoneInfo

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError

from src.core.config import get_settings
from src.tasks.repository import TaskRepository
from src.tasks.schemas import TaskReminderRead
from src.tasks.service import TaskService
from src.users.repository import UserRepository
from src.worker.celery_app import celery_app
from src.worker.database import worker_session_context

logger = logging.getLogger(__name__)


@celery_app.task(name="src.worker.tasks.send_deadline_reminders")
def send_deadline_reminders() -> dict[str, int]:
    return asyncio.run(_send_deadline_reminders())


async def _send_deadline_reminders() -> dict[str, int]:
    settings = get_settings()
    if not settings.bot_enabled:
        logger.info("BOT_TOKEN is not set. Deadline reminders are skipped.")
        return {"sent": 0, "failed": 0, "skipped": 1}

    async with worker_session_context() as session:
        service = TaskService(TaskRepository(session), UserRepository(session))
        reminders = await service.list_deadline_reminders()

        bot = Bot(
            token=settings.bot_token or "",
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        sent = 0
        failed = 0

        try:
            for reminder in reminders:
                try:
                    await bot.send_message(
                        chat_id=reminder.creator_tg_id,
                        text=format_reminder(reminder),
                    )
                    await service.mark_reminder_sent(reminder.id)
                    sent += 1
                except TelegramAPIError:
                    failed += 1
                    logger.exception("Failed to send reminder for task %s", reminder.id)
        finally:
            await bot.session.close()

    return {"sent": sent, "failed": failed, "skipped": 0}


def format_reminder(reminder: TaskReminderRead) -> str:
    settings = get_settings()
    deadline = reminder.deadline.astimezone(ZoneInfo(settings.timezone)).strftime("%Y-%m-%d %H:%M")
    return (
        "⏰ <b>Напоминание о дедлайне</b>\n\n"
        f"Через час дедлайн по задаче:\n<b>{escape(reminder.title)}</b>\n\n"
        f"🗓 Дедлайн: <code>{deadline}</code>"
    )
