from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete

from models.post import PostModel
from schemas.post import PostCreate, PostUpdate


async def create_post(session: AsyncSession, post_in: PostCreate) -> PostModel:
    new_post = PostModel(**post_in.model_dump())
    session.add(new_post)
    await session.commit()
    await session.refresh(new_post)
    return new_post


async def get_post_by_id(session: AsyncSession, post_id: int) -> PostModel | None:
    result = await session.execute(select(PostModel).where(PostModel.id == post_id))
    return result.scalar_one_or_none()


async def get_all_posts(session: AsyncSession) -> list[PostModel]:
    result = await session.execute(select(PostModel))
    return result.scalars().all()


async def get_posts_by_source_id(session: AsyncSession, source_id: int) -> list[PostModel]:
    result = await session.execute(select(PostModel).where(PostModel.source_id == source_id))
    return result.scalars().all()


async def get_posts_by_status(session: AsyncSession, status: str) -> list[PostModel]:
    result = await session.execute(select(PostModel).where(PostModel.status == status))
    return result.scalars().all()

async def update_post(session: AsyncSession, post_id: int, post_in: PostUpdate) -> PostModel | None:
    result = await session.execute(select(PostModel).where(PostModel.id == post_id))
    post = result.scalar_one_or_none()

    if not post:
        return None

    for key, value in post_in.model_dump(exclude_unset=True).items():
        setattr(post, key, value)

    await session.commit()
    await session.refresh(post)
    return post


async def delete_post(session: AsyncSession, post_id: int) -> bool:
    result = await session.execute(delete(PostModel).where(PostModel.id == post_id))
    await session.commit()
    return result.rowcount > 0


async def delete_posts_by_source_id(session: AsyncSession, source_id: int) -> bool:
    result = await session.execute(delete(PostModel).where(PostModel.source_id == source_id))
    await session.commit()
    return result.rowcount > 0
