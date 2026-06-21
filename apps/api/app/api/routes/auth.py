from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.auth import get_current_user
from app.core.config import Settings, get_settings
from app.core.cookies import clear_auth_cookie, set_auth_cookie
from app.core.security import create_access_token
from app.db.models.user import User
from app.db.session import get_db_session
from app.schemas.auth import LoginRequest, UserResponse
from app.services.users import authenticate_user, mark_user_login

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=UserResponse)
async def login(
    payload: LoginRequest,
    response: Response,
    session: AsyncSession = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
) -> UserResponse:
    user = await authenticate_user(session, payload.email, payload.password)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    token = create_access_token(user.id, settings)
    set_auth_cookie(response, token, settings)
    await mark_user_login(session, user)
    return UserResponse.model_validate(user)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    settings: Settings = Depends(get_settings),
) -> Response:
    clear_auth_cookie(response, settings)
    response.status_code = status.HTTP_204_NO_CONTENT
    return response


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
