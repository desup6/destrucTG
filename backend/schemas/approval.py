from pydantic import BaseModel
from typing import Optional

class ApprovalCreate(BaseModel):
    admin_id: int
    message_telegram_id: int
    post_id: int
    liked: Optional[bool] = None

class ApprovalUpdate(BaseModel):
    liked: bool

class ApprovalRead(BaseModel):
    admin_id: int
    message_telegram_id: int
    post_id: int
    liked: Optional[bool]

    class Config:
        orm_mode = True
