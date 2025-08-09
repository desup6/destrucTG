from pydantic import BaseModel

class SettingCreate(BaseModel):
    name: str
    value: str

class SettingUpdate(BaseModel):
    value: str

class SettingRead(BaseModel):
    name: str
    value: str

    class Config:
        orm_mode = True
