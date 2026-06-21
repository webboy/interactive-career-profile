from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password
from app.db.models.user import User


async def get_user_by_id(session: AsyncSession, user_id: int) -> User | None:
    result = await session.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def authenticate_user(session: AsyncSession, email: str, password: str) -> User | None:
    user = await get_user_by_email(session, email)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user


async def create_user(session: AsyncSession, email: str, password: str) -> User:
    user = User(email=email, password_hash=hash_password(password), is_active=True)
    session.add(user)
    await session.commit()
    await session.refresh(user)
    return user


async def update_user_password(session: AsyncSession, user: User, password: str) -> User:
    user.password_hash = hash_password(password)
    await session.commit()
    await session.refresh(user)
    return user


async def mark_user_login(session: AsyncSession, user: User) -> None:
    user.last_login_at = datetime.now(timezone.utc)
    await session.commit()
