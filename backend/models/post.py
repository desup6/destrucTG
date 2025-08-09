from sqlalchemy import Column, Integer, Text, String, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from db.db import Base 

class PostModel(Base):
    __tablename__ = "posts"

    id = Column(Integer, primary_key=True)
    source_id = Column(Integer, ForeignKey("sources.id"), nullable=False)
    telegram_text = Column(Text, nullable=False)
    media_paths = Column(ARRAY(String), nullable=True)
    status = Column(String, nullable=False)
    scheduled_at = Column(DateTime(timezone=True), nullable=True)
    posted_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
