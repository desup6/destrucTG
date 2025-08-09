from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from models.approval import ApprovalModel
from schemas.approval import ApprovalCreate, ApprovalUpdate

async def create_approval(session: AsyncSession, approval_in: ApprovalCreate) -> ApprovalModel:
    new_approval = ApprovalModel(**approval_in.model_dump())
    session.add(new_approval)
    await session.commit()
    await session.refresh(new_approval)
    return new_approval

async def get_approvals_by_admin_id(session: AsyncSession, admin_id: int) -> list[ApprovalModel] | None:
    result = await session.execute(select(ApprovalModel).where(ApprovalModel.admin_id == admin_id))
    return result.scalars.all()

async def get_approvals_by_post_id(session: AsyncSession, post_id: int) -> list[ApprovalModel] | None:
    result = await session.execute(select(ApprovalModel).where(ApprovalModel.post_id == post_id))
    return result.scalars.all()

async def get_all_approvals(session: AsyncSession) -> list[ApprovalModel]:
    result = await session.execute(select(ApprovalModel))
    return result.scalars.all()

async def update_approval(session: AsyncSession, admin_id: int, message_telegram_id: int, approval_in: ApprovalUpdate) -> ApprovalModel | None:
    result = await session.execute(select(ApprovalModel).where((ApprovalModel.admin_id == admin_id) & (ApprovalModel.message_telegram_id == message_telegram_id)))
    approval = result.scalar_one_or_none()

    if not approval:
        return None
    
    for key, value in approval_in.model_dump(exclude_unset=True).items():
        setattr(approval, key, value)

    await session.commit()
    await session.refresh(approval)
    return approval

async def delete_approval_by_admin_id(session: AsyncSession, admin_id: int) -> bool:
    result = await session.execute(delete(ApprovalModel).where(ApprovalModel.admin_id == admin_id))
    await session.commit()

    return result.rowcount > 0


async def delete_approval_by_post_id(session: AsyncSession, post_id: int) -> bool:
    result = await session.execute(delete(ApprovalModel).where(ApprovalModel.post_id == post_id))
    await session.commit()

    return result.rowcount > 0