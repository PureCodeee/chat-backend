from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password
from app.core.security import verify_password


async def create_user(db: AsyncSession, user_in: UserCreate) -> User:
    # проверка уникальности
    result = await db.execute(
        select(User).where(User.username == user_in.username)
    )
    existing = result.scalar_one_or_none()
    if existing:
        raise ValueError("Username already exists")

    user = User(
        username=user_in.username,
        hashed_password=hash_password(user_in.password),
    )

    db.add(user)
    await db.commit()
    await db.refresh(user)

    return user


async def authenticate_user(
    db: AsyncSession, username: str, password: str
) -> User | None:
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()
    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user