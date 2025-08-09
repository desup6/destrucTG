from pydantic import BaseModel

class AdminCreate(BaseModel):
    telegram_id: int
    is_subscribed: bool
    is_superuser: bool

class AdminUpdate(BaseModel):
    is_subscribed: bool
    is_superuser: bool

class AdminRead(BaseModel):
    telegram_id: int
    is_subscribed: bool
    is_superuser: bool

    class Config:
        orm_mode = True
