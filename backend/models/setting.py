from sqlalchemy import Column, String
from db.db import Base

class SettingModel(Base):
    __tablename__ = "settings"

    name = Column(String, primary_key=True)
    value = Column(String, nullable=False)
