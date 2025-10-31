from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from datetime import datetime
from core.database import get_db
from model.chat_model import ChatMessageModel
from model.auth_model import User
from utils.websocket_manager import manager

router = APIRouter()


@router.websocket("/ws/{sender}/{receiver}")
async def chat_websocket(websocket: WebSocket, sender: str, receiver: str, db: Session = Depends(get_db)):
    """
    WebSocket endpoint for chatting between two users (sender ↔ receiver)
    """
    await manager.connect(sender, websocket)
    await manager.set_active_chat(sender, receiver)

    try:
        while True:
            data = await websocket.receive_json()
            message_text = data.get("message")

            # Fetch sender and receiver from DB
            sender_user = db.query(User).filter(User.username == sender).first()
            receiver_user = db.query(User).filter(User.username == receiver).first()

            if not sender_user or not receiver_user:
                continue

            # Save message in DB
            new_message = ChatMessageModel(
                sender_id=sender_user.id,
                receiver_id=receiver_user.id,
                content=message_text,
                timestamp=datetime.now(),
            )
            db.add(new_message)
            db.commit()

            # Prepare message payload
            message_data = {
                "type": "chat",
                "sender": sender,
                "receiver": receiver,
                "message": message_text,
                "timestamp": str(new_message.timestamp),
            }

            # Send message (and notification if needed)
            await manager.send_personal_message(message_data, sender, receiver)

    except WebSocketDisconnect:
        manager.disconnect(sender)
        await manager.set_active_chat(sender, None)
        print(f"❌ {sender} disconnected from chat with {receiver}")


@router.websocket("/ws/notify/{username}")
async def notify_websocket(websocket: WebSocket, username: str):
    """
    Global WebSocket connection for user notifications
    (when user is online but not in a specific chat)
    """
    await manager.connect(username, websocket)
    await manager.set_active_chat(username, None)

    try:
        while True:
            await websocket.receive_text()  # Keep connection alive
    except WebSocketDisconnect:
        manager.disconnect(username)
        await manager.set_active_chat(username, None)
        print(f"🔕 {username} notification socket disconnected.")


@router.get("/messages/{sender}/{receiver}")
def get_chat_history(sender: str, receiver: str, db: Session = Depends(get_db)):
    """
    Fetch complete chat history between two users.
    """
    sender_user = db.query(User).filter(User.username == sender).first()
    receiver_user = db.query(User).filter(User.username == receiver).first()

    if not sender_user or not receiver_user:
        return []

    messages = (
        db.query(ChatMessageModel)
        .filter(
            ((ChatMessageModel.sender_id == sender_user.id) & (ChatMessageModel.receiver_id == receiver_user.id))
            | ((ChatMessageModel.sender_id == receiver_user.id) & (ChatMessageModel.receiver_id == sender_user.id))
        )
        .order_by(ChatMessageModel.timestamp.asc())
        .all()
    )

    return [
        {
            "sender": m.sender.username,
            "receiver": m.receiver.username,
            "message": m.content,
            "timestamp": m.timestamp,
        }
        for m in messages
    ]
