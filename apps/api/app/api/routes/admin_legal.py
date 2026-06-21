from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import require_admin_user
from app.db.models.user import User
from app.db.session import get_db_session
from app.schemas.legal import LegalPageResponse, LegalPageUpdateRequest
from app.services.legal_pages import get_legal_page, is_valid_legal_slug, update_legal_page

router = APIRouter(prefix="/api/admin/legal-pages", tags=["admin-legal"])


@router.get("/{slug}", response_model=LegalPageResponse)
async def admin_get_legal_page(
    slug: str,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> LegalPageResponse:
    if not is_valid_legal_slug(slug):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legal page not found")

    page = await get_legal_page(session, slug)
    if page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legal page not found")

    return LegalPageResponse.model_validate(page)


@router.put("/{slug}", response_model=LegalPageResponse)
async def admin_update_legal_page(
    slug: str,
    payload: LegalPageUpdateRequest,
    _: User = Depends(require_admin_user),
    session: AsyncSession = Depends(get_db_session),
) -> LegalPageResponse:
    if not is_valid_legal_slug(slug):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legal page not found")

    page = await update_legal_page(session, slug, payload.title, payload.content)
    if page is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Legal page not found")

    return LegalPageResponse.model_validate(page)
