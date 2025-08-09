from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from models.setting import SettingModel
from schemas.setting import SettingCreate, SettingUpdate


async def create_setting(session: AsyncSession, setting_in: SettingCreate) -> SettingModel:
    new_setting = SettingModel(**setting_in.model_dump())
    session.add(new_setting)
    await session.commit()
    await session.refresh(new_setting)
    return new_setting


async def get_setting_by_name(session: AsyncSession, name: str) -> SettingModel | None:
    result = await session.execute(select(SettingModel).where(SettingModel.name == name))
    return result.scalar_one_or_none()


async def get_all_settings(session: AsyncSession) -> list[SettingModel]:
    result = await session.execute(select(SettingModel))
    return result.scalars().all()


async def update_setting(session: AsyncSession, name: str, setting_in: SettingUpdate) -> SettingModel | None:
    result = await session.execute(select(SettingModel).where(SettingModel.name == name))
    setting = result.scalar_one_or_none()

    if not setting:
        return None

    for key, value in setting_in.model_dump(exclude_unset=True).items():
        setattr(setting, key, value)

    await session.commit()
    await session.refresh(setting)
    return setting


async def delete_setting(session: AsyncSession, name: str) -> bool:
    result = await session.execute(delete(SettingModel).where(SettingModel.name == name))
    await session.commit()
    return result.rowcount > 0
