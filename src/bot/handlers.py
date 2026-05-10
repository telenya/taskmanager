from datetime import datetime
from html import escape
from zoneinfo import ZoneInfo

from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

from src.bot.dependencies import task_service_context, user_service_context
from src.bot.keyboards import (
    MENU_ADD_TASK,
    MENU_CANCEL,
    MENU_HOME,
    MENU_MY_TASKS,
    TASKS_REFRESH,
    back_to_menu_keyboard,
    cancel_keyboard,
    main_menu_keyboard,
    task_created_keyboard,
    task_list_keyboard,
)
from src.bot.states import AddTaskState
from src.core.config import get_settings
from src.core.exceptions import ForbiddenError, NotFoundError
from src.tasks.enums import TaskStatus
from src.tasks.schemas import TaskCreate, TaskList, TaskRead, TaskStatusChange
from src.users.schemas import UserRead

router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    user = message.from_user
    if user is None:
        return

    db_user = await register_user(user.id, user.username)

    await message.answer(
        "👋 <b>Добро пожаловать в Task Manager</b>\n\n"
        "Здесь можно быстро создавать задачи, смотреть список дел "
        "и менять статус одним нажатием.\n\n"
        f"🆔 Ваш внутренний id: <code>{db_user.id}</code>\n"
        "Выберите действие:",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("cancel"))
async def cancel(message: Message, state: FSMContext) -> None:
    await state.clear()
    await message.answer(
        "✖️ Действие отменено.",
        reply_markup=main_menu_keyboard(),
    )


@router.message(Command("add_task"))
async def add_task(message: Message, state: FSMContext) -> None:
    await ask_task_title(message, state)


@router.callback_query(F.data == MENU_HOME)
async def menu_home(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer()
    if callback.message:
        await callback.message.answer(
            "🏠 <b>Главное меню</b>\n\nЧто делаем дальше?",
            reply_markup=main_menu_keyboard(),
        )


@router.callback_query(F.data == MENU_CANCEL)
async def menu_cancel(callback: CallbackQuery, state: FSMContext) -> None:
    await state.clear()
    await callback.answer("Отменено")
    if callback.message:
        await callback.message.answer(
            "✖️ Действие отменено.",
            reply_markup=main_menu_keyboard(),
        )


@router.callback_query(F.data == MENU_ADD_TASK)
async def menu_add_task(callback: CallbackQuery, state: FSMContext) -> None:
    await callback.answer()
    if callback.message:
        await ask_task_title(callback.message, state)


@router.message(AddTaskState.title, F.text)
async def add_task_title(message: Message, state: FSMContext) -> None:
    title = (message.text or "").strip()
    if not title:
        await message.answer(
            "Название не может быть пустым.",
            reply_markup=cancel_keyboard(),
        )
        return
    if len(title) > 200:
        await message.answer(
            "Название слишком длинное. Максимум 200 символов.",
        )
        return

    await state.update_data(title=title)
    await state.set_state(AddTaskState.description)
    await message.answer(
        "📝 <b>Описание</b>\n\n"
        "Отправьте описание задачи.\n"
        "Если оно не нужно, отправьте <code>-</code>.",
        reply_markup=cancel_keyboard(),
    )


@router.message(AddTaskState.description, F.text)
async def add_task_description(message: Message, state: FSMContext) -> None:
    raw_description = (message.text or "").strip()
    description = None if raw_description in {"", "-", "skip"} else raw_description

    await state.update_data(description=description)
    await state.set_state(AddTaskState.deadline)
    await message.answer(
        "🗓 <b>Дедлайн</b>\n\n"
        "Отправьте дату и время.\n"
        "Формат: <code>2026-05-10 18:30</code> или ISO 8601.",
        reply_markup=cancel_keyboard(),
    )


@router.message(AddTaskState.deadline, F.text)
async def add_task_deadline(message: Message, state: FSMContext) -> None:
    user = message.from_user
    if user is None:
        return

    try:
        deadline = parse_deadline(message.text or "")
    except ValueError:
        await message.answer(
            "Не получилось разобрать дедлайн.\n"
            "Пример: <code>2026-05-10 18:30</code>",
            reply_markup=cancel_keyboard(),
        )
        return

    state_data = await state.get_data()
    db_user = await register_user(user.id, user.username)

    async with task_service_context() as task_service:
        task = await task_service.create_task(
            TaskCreate(
                title=state_data["title"],
                description=state_data.get("description"),
                deadline=deadline,
                creator_id=db_user.id,
            )
        )

    await state.clear()
    await message.answer(
        f"✅ <b>Задача создана</b>\n\n{format_task(task)}",
        reply_markup=task_created_keyboard(task.id),
    )


@router.message(Command("my_tasks"))
async def my_tasks(message: Message) -> None:
    user = message.from_user
    if user is None:
        return

    await show_my_tasks(message, user.id, user.username)


@router.callback_query(F.data == MENU_MY_TASKS)
@router.callback_query(F.data == TASKS_REFRESH)
async def menu_my_tasks(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message:
        await show_my_tasks(callback.message, callback.from_user.id, callback.from_user.username)


@router.callback_query(F.data.startswith("task:status:"))
async def change_task_status(callback: CallbackQuery) -> None:
    if callback.data is None:
        await callback.answer()
        return

    try:
        _, _, raw_task_id, raw_status = callback.data.split(":", maxsplit=3)
        task_id = int(raw_task_id)
        status = TaskStatus(raw_status)
    except ValueError:
        await callback.answer("Некорректное действие", show_alert=True)
        return

    db_user = await register_user(callback.from_user.id, callback.from_user.username)

    try:
        async with task_service_context() as task_service:
            task = await task_service.change_task_status(
                task_id,
                TaskStatusChange(actor_user_id=db_user.id, status=status),
            )
    except (ForbiddenError, NotFoundError) as exc:
        await callback.answer(translate_error(exc.message), show_alert=True)
        return

    await callback.answer("Статус обновлен")
    if callback.message:
        await callback.message.answer(
            f"✨ <b>Статус обновлен</b>\n\n{format_task(task)}",
            reply_markup=back_to_menu_keyboard(),
        )


async def ask_task_title(message: Message, state: FSMContext) -> None:
    await state.set_state(AddTaskState.title)
    await message.answer(
        "➕ <b>Новая задача</b>\n\n"
        "Отправьте название задачи одним сообщением.",
        reply_markup=cancel_keyboard(),
    )


async def register_user(tg_id: int, username: str | None) -> UserRead:
    async with user_service_context() as service:
        return await service.get_or_create_by_tg_id(tg_id, username)


async def show_my_tasks(message: Message, tg_id: int, username: str | None) -> None:
    await register_user(tg_id, username)

    try:
        async with task_service_context() as task_service:
            tasks = await task_service.list_tasks_by_tg_id(tg_id)
    except NotFoundError:
        await message.answer("📭 Задач пока нет.", reply_markup=main_menu_keyboard())
        return

    if not tasks.items:
        await message.answer(
            "📭 <b>Задач пока нет</b>\n\n"
            "Можно создать первую прямо сейчас:",
            reply_markup=main_menu_keyboard(),
        )
        return

    await message.answer(format_task_list(tasks), reply_markup=task_list_keyboard(tasks.items))


def parse_deadline(raw_value: str) -> datetime:
    settings = get_settings()
    timezone = ZoneInfo(settings.timezone)
    value = raw_value.strip()

    for date_format in ("%Y-%m-%d %H:%M", "%d.%m.%Y %H:%M"):
        try:
            return datetime.strptime(value, date_format).replace(tzinfo=timezone)
        except ValueError:
            continue

    parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=timezone)
    return parsed


def format_task(task: TaskRead) -> str:
    settings = get_settings()
    deadline = task.deadline.astimezone(ZoneInfo(settings.timezone)).strftime("%Y-%m-%d %H:%M")
    description = f"\n\n📝 {escape(task.description)}" if task.description else ""
    return (
        f"{status_icon(task.status)} <b>#{task.id} {escape(task.title)}</b>{description}\n\n"
        f"📌 Статус: <code>{status_label(task.status)}</code>\n"
        f"🗓 Дедлайн: <code>{deadline}</code>"
    )


def format_task_list(tasks: TaskList) -> str:
    shown_tasks = tasks.items[:10]
    rendered_tasks = "\n\n".join(format_task(task) for task in shown_tasks)
    tail = ""
    if tasks.total > len(shown_tasks):
        tail = (
            f"\n\nПоказаны первые {len(shown_tasks)} "
            f"из {tasks.total} задач."
        )
    return f"📋 <b>Ваши задачи</b>\n\n{rendered_tasks}{tail}"


def status_icon(status: TaskStatus) -> str:
    return {
        TaskStatus.PENDING: "🕓",
        TaskStatus.IN_PROGRESS: "🔧",
        TaskStatus.DONE: "✅",
    }[status]


def status_label(status: TaskStatus) -> str:
    return {
        TaskStatus.PENDING: "ожидает",
        TaskStatus.IN_PROGRESS: "в работе",
        TaskStatus.DONE: "готово",
    }[status]


def translate_error(message: str) -> str:
    return {
        "Only the creator can change task status": (
            "Можно менять только свои задачи"
        ),
        "Task not found": "Задача не найдена",
        "Actor user not found": "Пользователь не найден",
    }.get(message, message)
