from sqlalchemy import Column, Integer, BigInteger, Boolean
from db.db import Base

class AdminModel(Base):
    __tablename__ = "admins"

    telegram_id = Column(BigInteger, primary_key=True)
    is_superuser = Column(Boolean, nullable=False)
    is_subscribed = Column(Boolean, nullable=False)
