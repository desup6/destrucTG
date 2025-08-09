from sqlalchemy import Column, Integer, String
from db.db import Base

class FolderModel(Base):
    __tablename__ = "folders"

    id = Column(Integer, primary_key=True)
    title = Column(String, nullable=False)
