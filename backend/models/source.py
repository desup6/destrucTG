from sqlalchemy import Column, Integer, BigInteger, String, ForeignKey
from db.db import Base

class SourceModel(Base):
    __tablename__ = "sources"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, nullable=False)
    title = Column(String, nullable=False)
    chance = Column(Integer, nullable=False)
    folder_id = Column(Integer, ForeignKey("folders.id"), nullable=True)
