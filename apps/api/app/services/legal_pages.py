from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models.legal_page import LegalPage

VALID_LEGAL_SLUGS = frozenset({"privacy", "terms"})


def is_valid_legal_slug(slug: str) -> bool:
    return slug in VALID_LEGAL_SLUGS


async def get_legal_page(session: AsyncSession, slug: str) -> LegalPage | None:
    result = await session.execute(select(LegalPage).where(LegalPage.slug == slug))
    return result.scalar_one_or_none()


async def update_legal_page(
    session: AsyncSession,
    slug: str,
    title: str,
    content: str,
) -> LegalPage | None:
    page = await get_legal_page(session, slug)
    if page is None:
        return None

    page.title = title
    page.content = content
    await session.commit()
    await session.refresh(page)
    return page
