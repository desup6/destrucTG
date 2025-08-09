from pydantic import BaseModel

class FolderCreate(BaseModel):
    title: str

class FolderUpdate(BaseModel):
    title: str

class FolderRead(BaseModel):
    id: int
    title: str

    class Config:
        orm_mode = True
