from aiogram.fsm.state import State, StatesGroup


class AddTaskState(StatesGroup):
    title = State()
    description = State()
    deadline = State()
