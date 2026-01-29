from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.chat_participant import ChatParticipant
from app.db.session import async_session_maker
from app.websockets.manager import ConnectionManager
from app.websockets.auth import get_user_from_token
from app.services.message_service import create_message
from app.models.user import User

router = APIRouter()
manager = ConnectionManager()


@router.websocket("/ws/chats/{chat_id}")
async def websocket_chat(websocket: WebSocket, chat_id: int):
    # Получаем токен из query params
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        return

    async with async_session_maker() as db:
        user = await get_user_from_token(token, db)
        if not user:
            await websocket.close(code=1008)
            return

        # Проверяем, что пользователь участник чата
        result = await db.execute(
            select(ChatParticipant).where(
                ChatParticipant.chat_id == chat_id,
                ChatParticipant.user_id == user.id,
            )
        )
        if result.scalar_one_or_none() is None:
            await websocket.close(code=1008)
            return


        await manager.connect(chat_id, websocket)

        await manager.broadcast(
            chat_id,
            {
                "type": "system",
                "message": f"{user.username} joined the chat"
            }
        )

        try:
            while True:
                data = await websocket.receive_json()
                content = data.get("content")
                if not content:
                    continue

                # Сохраняем сообщение в БД
                msg = await create_message(
                    db,
                    chat_id=chat_id,
                    sender_id=user.id,
                    content=content,
                )

                result = await db.execute(
                    select(User.username).where(User.id == msg.sender_id)
                )
                sender_username = result.scalar_one()

                # Рассылаем всем в чате
                await manager.broadcast(
                            chat_id,
                            {
                                "id": msg.id,
                                "chat_id": chat_id,
                                "sender": sender_username,
                                "content": msg.content,
                                "created_at": str(msg.created_at),
                            },
                        )


        except WebSocketDisconnect:
            manager.disconnect(chat_id, websocket)
            await manager.broadcast(
                chat_id,
                {
                    "type": "system",
                    "message": f"{user.username} left the chat"
                }
            )
