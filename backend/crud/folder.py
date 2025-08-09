from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from models.folder import FolderModel
from schemas.folder import FolderCreate, FolderUpdate


async def create_folder(session: AsyncSession, folder_in: FolderCreate) -> FolderModel:
    new_folder = FolderModel(**folder_in.model_dump())
    session.add(new_folder)
    await session.commit()
    await session.refresh(new_folder)
    return new_folder


async def get_folder_by_id(session: AsyncSession, folder_id: int) -> FolderModel | None:
    result = await session.execute(select(FolderModel).where(FolderModel.id == folder_id))
    return result.scalar_one_or_none()


async def get_all_folders(session: AsyncSession) -> list[FolderModel]:
    result = await session.execute(select(FolderModel))
    return result.scalars().all()


async def update_folder(session: AsyncSession, folder_id: int, folder_in: FolderUpdate) -> FolderModel | None:
    result = await session.execute(select(FolderModel).where(FolderModel.id == folder_id))
    folder = result.scalar_one_or_none()

    if not folder:
        return None

    for key, value in folder_in.model_dump(exclude_unset=True).items():
        setattr(folder, key, value)

    await session.commit()
    await session.refresh(folder)
    return folder


async def delete_folder(session: AsyncSession, folder_id: int) -> bool:
    result = await session.execute(delete(FolderModel).where(FolderModel.id == folder_id))
    await session.commit()

    return result.rowcount > 0
