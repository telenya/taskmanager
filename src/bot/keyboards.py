from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.tasks.enums import TaskStatus
from src.tasks.schemas import TaskRead

MENU_ADD_TASK = "menu:add_task"
MENU_MY_TASKS = "menu:my_tasks"
MENU_HOME = "menu:home"
MENU_CANCEL = "menu:cancel"
TASKS_REFRESH = "tasks:refresh"


def main_menu_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="➕ Создать задачу", callback_data=MENU_ADD_TASK)
    builder.button(text="📋 Мои задачи", callback_data=MENU_MY_TASKS)
    builder.adjust(1)
    return builder.as_markup()


def cancel_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✖️ Отменить", callback_data=MENU_CANCEL)],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MENU_HOME)],
        ]
    )


def back_to_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📋 Мои задачи", callback_data=MENU_MY_TASKS)],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MENU_HOME)],
        ]
    )


def task_list_keyboard(tasks: list[TaskRead]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for task in tasks[:10]:
        if task.status == TaskStatus.DONE:
            continue
        builder.row(
            InlineKeyboardButton(
                text=f"▶️ В работу #{task.id}",
                callback_data=_task_status_callback(task.id, TaskStatus.IN_PROGRESS),
            ),
            InlineKeyboardButton(
                text=f"✅ Готово #{task.id}",
                callback_data=_task_status_callback(task.id, TaskStatus.DONE),
            ),
        )

    builder.row(
        InlineKeyboardButton(text="🔄 Обновить", callback_data=TASKS_REFRESH),
        InlineKeyboardButton(text="🏠 Меню", callback_data=MENU_HOME),
    )
    return builder.as_markup()


def task_created_keyboard(task_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="▶️ В работу",
                    callback_data=_task_status_callback(task_id, TaskStatus.IN_PROGRESS),
                ),
                InlineKeyboardButton(
                    text="✅ Закрыть",
                    callback_data=_task_status_callback(task_id, TaskStatus.DONE),
                ),
            ],
            [InlineKeyboardButton(text="📋 Мои задачи", callback_data=MENU_MY_TASKS)],
            [InlineKeyboardButton(text="🏠 Главное меню", callback_data=MENU_HOME)],
        ]
    )


def _task_status_callback(task_id: int, status: TaskStatus) -> str:
    return f"task:status:{task_id}:{status.value}"
