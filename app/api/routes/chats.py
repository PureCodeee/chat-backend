from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete


from app.api.deps import get_current_user
from app.db.session import get_db
from app.schemas.chat import ChatOut
from app.schemas.message import MessageCreate, MessageOut
from app.services.chat_service import create_chat, get_user_chats
from app.services.message_service import create_message, get_chat_messages
from app.models.chat import Chat
from app.models.chat_participant import ChatParticipant
from app.models.user import User




router = APIRouter(prefix="/chats", tags=["chats"])


@router.post("/{other_user_id}", response_model=ChatOut)
async def create_chat_with_user(
    other_user_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chat = await create_chat(db, current_user.id, other_user_id)
    return chat


@router.get("/", response_model=list[ChatOut])
async def list_my_chats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    chats = await get_user_chats(db, current_user.id)
    return chats


@router.post("/{chat_id}/messages", response_model=MessageOut)
async def send_message(
    chat_id: int,
    data: MessageCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        msg = await create_message(
            db,
            chat_id=chat_id,
            sender_id=current_user.id,
            content=data.content,
        )
        return msg
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not a participant")


@router.get("/{chat_id}/messages", response_model=list[MessageOut])
async def list_messages(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        return await get_chat_messages(db, chat_id, current_user.id)
    except PermissionError:
        raise HTTPException(status_code=403, detail="Not a participant")
    

@router.post("/by-username/{username}")
async def get_or_create_chat_by_username(
    username: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # найти второго пользователя
    result = await db.execute(
        select(User).where(User.username == username)
    )
    other_user = result.scalar_one_or_none()

    if not other_user:
        raise HTTPException(status_code=404, detail="User not found")

    # попробовать найти существующий чат
    result = await db.execute(
        select(ChatParticipant.chat_id)
        .where(ChatParticipant.user_id == current_user.id)
    )
    my_chat_ids = {row[0] for row in result.all()}

    if my_chat_ids:
        result = await db.execute(
            select(ChatParticipant.chat_id)
            .where(
                ChatParticipant.user_id == other_user.id,
                ChatParticipant.chat_id.in_(my_chat_ids),
            )
        )
        row = result.first()
        if row:
            return {"id": row[0], "existing": True}

    # иначе создать новый
    try:
        chat = await create_chat(db, current_user.id, other_user.id)
        return {"id": chat.id, "existing": False}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/my")
async def get_my_chats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Chat.id)
        .join(ChatParticipant)
        .where(ChatParticipant.user_id == current_user.id)
    )
    chat_ids = [row[0] for row in result.all()]

    chats = []
    for chat_id in chat_ids:
        # получить другого участника
        result = await db.execute(
            select(User.username)
            .join(ChatParticipant, ChatParticipant.user_id == User.id)
            .where(
                ChatParticipant.chat_id == chat_id,
                User.id != current_user.id
            )
        )
        other_username = result.scalar_one_or_none()
        chats.append({
            "id": chat_id,
            "other_username": other_username
        })

    return chats


@router.post("/{chat_id}/leave")
async def leave_chat(
    chat_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await db.execute(
        delete(ChatParticipant).where(
            ChatParticipant.chat_id == chat_id,
            ChatParticipant.user_id == current_user.id,
        )
    )
    await db.commit()
    return {"status": "left"}
