from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.version import API_VERSION
from app.db.session import get_db_session
from app.services.version import get_api_version

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check(session: AsyncSession = Depends(get_db_session)) -> JSONResponse:
    try:
        version = await get_api_version(session)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content={
                "status": "ok",
                "service": "api",
                "version": version,
                "database": "connected",
            },
        )
    except Exception:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "degraded",
                "service": "api",
                "version": API_VERSION,
                "database": "unavailable",
            },
        )
