from sqlalchemy import Column, Integer, BigInteger, Boolean, ForeignKey
from db.db import Base

class ApprovalModel(Base):
    __tablename__ = "approvals"

    admin_telegram_id = Column(Integer, ForeignKey("admins.telegram_id"), primary_key=True)
    message_telegram_id = Column(Integer, primary_key=True)
    post_id = Column(Integer, ForeignKey(("posts.id")), nullable=False)
    liked = Column(Boolean, nullable=True)
