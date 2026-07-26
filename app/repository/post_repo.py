from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Post, PostStatus
from app.utils.datetime import utc_now_naive


class PostRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, news_id: str, generated_text: str) -> Post:
        post = Post(
            news_id=news_id,
            generated_text=generated_text,
            status=PostStatus.PENDING
        )
        self.session.add(post)
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def get_by_id(self, post_id: int) -> Post | None:
        return await self.session.get(Post, post_id)

    async def get_by_news_id(self, news_id: str) -> Post | None:
        result = await self.session.execute(
            select(Post).where(Post.news_id == news_id)
        )
        return result.scalar_one_or_none()

    async def get_pending(self, limit: int = 10) -> list[Post]:
        result = await self.session.execute(
            select(Post).where(Post.status == PostStatus.PENDING)
            .order_by(Post.created_at)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def update_status(self,
                            post_id: int,
                            status: PostStatus,
                            error_message: str | None = None)-> Post| None:
        post = await self.session.get(Post, post_id)
        if post is None:
            return None
        post.status = status
        post.error_message = error_message
        post.published_at = (
            utc_now_naive()
            if status == PostStatus.PUBLISHED
            else None
        )
        await self.session.commit()
        await self.session.refresh(post)
        return post

    async def exists_for_news(self, news_id: str) -> bool:
        result = await self.session.execute(
            select(Post.id).where(Post.news_id == news_id).limit(1)

        )
        return result.scalar_one_or_none() is not None

    async def get_exists_news_ids(self, news_ids: list[str]) -> set[str]:
        if not news_ids:
            return set()

        result = await self.session.execute(
            select(Post.news_id).where(Post.news_id.in_(news_ids))
        )
        return set(result.scalars().all())

    async def get_stats(self) -> dict[str, int]:
        result = await self.session.execute(
            select(Post.status, func.count(Post.id)).group_by(Post.status)
        )
        counts = {
            (
                status.value
                if isinstance(status, PostStatus)
                else str(status)

            ): count
                for status, count in result.all()

        }
        return {
            'total': sum(counts.values()),
            'pending': counts.get(PostStatus.PENDING.value, 0),
            'published': counts.get(PostStatus.PUBLISHED.value, 0),
            'failed': counts.get(PostStatus.FAILED.value, 0),

        }




