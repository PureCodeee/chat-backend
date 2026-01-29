'''chat_service.py'''
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.models.chat import Chat
from app.models.chat_participant import ChatParticipant


async def create_chat(db: AsyncSession, user_id: int, other_user_id: int) -> Chat:
    if user_id == other_user_id:
        raise ValueError("Cannot create chat with yourself")
    chat = Chat()
    db.add(chat)
    await db.flush()  # получаем chat.id

    p1 = ChatParticipant(chat_id=chat.id, user_id=user_id)
    p2 = ChatParticipant(chat_id=chat.id, user_id=other_user_id)

    db.add_all([p1, p2])
    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise ValueError("Chat already exists")

    await db.refresh(chat)

    return chat


async def get_user_chats(db: AsyncSession, user_id: int) -> list[Chat]:
    result = await db.execute(
        select(Chat)
        .join(ChatParticipant)
        .where(ChatParticipant.user_id == user_id)
    )
    return list(result.scalars().all())
