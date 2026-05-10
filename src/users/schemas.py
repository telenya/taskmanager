from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    tg_id: int = Field(gt=0)
    username: str | None = Field(default=None, max_length=64)


class UserUpdate(BaseModel):
    username: str | None = Field(default=None, max_length=64)


class UserRead(BaseModel):
    id: int
    tg_id: int
    username: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserList(BaseModel):
    items: list[UserRead]
    total: int
