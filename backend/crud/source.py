from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from models.source import SourceModel
from schemas.source import SourceCreate, SourceUpdate


async def create_source(session: AsyncSession, source_in: SourceCreate) -> SourceModel:
    new_source = SourceModel(**source_in.model_dump())
    session.add(new_source)
    await session.commit()
    await session.refresh(new_source)
    return new_source


async def get_source_by_id(session: AsyncSession, source_id: int) -> SourceModel | None:
    result = await session.execute(select(SourceModel).where(SourceModel.id == source_id))
    return result.scalar_one_or_none()


async def get_all_sources(session: AsyncSession) -> list[SourceModel]:
    result = await session.execute(select(SourceModel))
    return result.scalars().all()


async def get_sources_by_folder_id(session: AsyncSession, folder_id: int) -> list[SourceModel]:
    result = await session.execute(select(SourceModel).where(SourceModel.folder_id == folder_id))
    return result.scalars().all()


async def update_source(session: AsyncSession, source_id: int, source_in: SourceUpdate) -> SourceModel | None:
    result = await session.execute(select(SourceModel).where(SourceModel.id == source_id))
    source = result.scalar_one_or_none()

    if not source:
        return None

    for key, value in source_in.model_dump(exclude_unset=True).items():
        setattr(source, key, value)

    await session.commit()
    await session.refresh(source)
    return source


async def delete_source(session: AsyncSession, source_id: int) -> bool:
    result = await session.execute(delete(SourceModel).where(SourceModel.id == source_id))
    await session.commit()
    return result.rowcount > 0
