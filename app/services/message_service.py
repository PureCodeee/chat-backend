from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.message import Message
from app.models.chat_participant import ChatParticipant


async def create_message(
    db,
    chat_id: int,
    sender_id: int,
    content: str,
) -> Message:
    # Проверка, что пользователь участник чата
    result = await db.execute(
        select(ChatParticipant)
        .where(
            ChatParticipant.chat_id == chat_id,
            ChatParticipant.user_id == sender_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise PermissionError("Not a chat participant")

    msg = Message(
        chat_id=chat_id,
        sender_id=sender_id,
        content=content,
    )
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return msg


async def get_chat_messages(
    db,
    chat_id: int,
    user_id: int,
) -> list[Message]:
    # Проверяем, что пользователь участник чата
    result = await db.execute(
        select(ChatParticipant)
        .where(
            ChatParticipant.chat_id == chat_id,
            ChatParticipant.user_id == user_id,
        )
    )
    if result.scalar_one_or_none() is None:
        raise PermissionError("Not a chat participant")

    result = await db.execute(
        select(Message)
        .where(Message.chat_id == chat_id)
        .order_by(Message.created_at)
    )
    return list(result.scalars().all())