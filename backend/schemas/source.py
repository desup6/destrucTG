from pydantic import BaseModel
from typing import Optional

class SourceCreate(BaseModel):
    telegram_id: int
    title: str
    folder_id: Optional[int] = None

class SourceUpdate(BaseModel):
    title: Optional[str] = None
    folder_id: Optional[int] = None
    chance: Optional[int] = None

class SourceRead(BaseModel):
    id: int
    telegram_id: int
    title: str
    folder_id: Optional[int]

    class Config:
        orm_mode = True
