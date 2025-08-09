from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PostCreate(BaseModel):
    source_id: int
    telegram_text: str
    media_paths: Optional[List[str]] = None
    status: str
    scheduled_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None

class PostUpdate(BaseModel):
    telegram_text: Optional[str] = None
    media_paths: Optional[List[str]] = None
    status: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None

class PostRead(BaseModel):
    id: int
    source_id: int
    telegram_text: str
    media_paths: Optional[List[str]] = None
    status: str
    scheduled_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        orm_mode = True
