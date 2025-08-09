from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from models.admin import AdminModel
from schemas.admin import AdminCreate, AdminUpdate


async def create_admin(session: AsyncSession, admin_in: AdminCreate) -> AdminModel:
    new_admin = AdminModel(**admin_in.model_dump())
    session.add(new_admin)
    await session.commit()
    await session.refresh(new_admin)
    return new_admin


async def get_admin_by_telegram_id(session: AsyncSession, telegram_id: int) -> AdminModel | None:
    result = await session.execute(
        select(AdminModel).where(AdminModel.telegram_id == telegram_id)
    )
    return result.scalar_one_or_none()


async def get_all_admins(session: AsyncSession) -> list[AdminModel]:
    result = await session.execute(select(AdminModel))
    return result.scalars().all()


async def update_admin(session: AsyncSession, telegram_id: int, admin_in: AdminUpdate) -> AdminModel | None:
    result = await session.execute(
        select(AdminModel).where(AdminModel.telegram_id == telegram_id)
    )
    admin = result.scalar_one_or_none()

    if not admin:
        return None

    for key, value in admin_in.model_dump(exclude_unset=True).items():
        setattr(admin, key, value)

    await session.commit()
    await session.refresh(admin)
    return admin


async def delete_admin(session: AsyncSession, telegram_id: int) -> bool:
    result = await session.execute(delete(AdminModel).where(AdminModel.telegram_id == telegram_id))
    await session.commit()

    return result.rowcount > 0
