from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class PostSchema(BaseModel):
    id: Optional[int]
    source_id: int
    message_id: int
    telegram_text: str
    media_links: Optional[List[str]] = None
    status: str
    scheduled_at: Optional[datetime] = None
    posted_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        orm_mode = True
