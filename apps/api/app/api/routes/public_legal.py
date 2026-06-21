from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db_session
from app.schemas.legal import LegalPageResponse
from app.services.legal_pages import get_legal_page

router = APIRouter(prefix="/api/public", tags=["public"])


async def _get_public_legal_page(session: AsyncSession, slug: str) -> LegalPageResponse:
    page = await get_legal_page(session, slug)
    if page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legal page not found")
    return LegalPageResponse.model_validate(page)


@router.get("/privacy", response_model=LegalPageResponse)
async def get_privacy(
    session: AsyncSession = Depends(get_db_session),
) -> LegalPageResponse:
    return await _get_public_legal_page(session, "privacy")


@router.get("/terms", response_model=LegalPageResponse)
async def get_terms(
    session: AsyncSession = Depends(get_db_session),
) -> LegalPageResponse:
    return await _get_public_legal_page(session, "terms")
