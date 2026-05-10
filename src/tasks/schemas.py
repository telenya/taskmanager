from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from src.tasks.enums import TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    deadline: datetime
    creator_id: int = Field(gt=0)


class TaskUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=2000)
    deadline: datetime | None = None


class TaskStatusChange(BaseModel):
    actor_user_id: int = Field(gt=0)
    status: TaskStatus


class TaskClose(BaseModel):
    actor_user_id: int = Field(gt=0)


class TaskRead(BaseModel):
    id: int
    title: str
    description: str | None
    status: TaskStatus
    deadline: datetime
    creator_id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TaskList(BaseModel):
    items: list[TaskRead]
    total: int


class TaskReminderRead(BaseModel):
    id: int
    title: str
    deadline: datetime
    creator_id: int
    creator_tg_id: int
    creator_username: str | None
