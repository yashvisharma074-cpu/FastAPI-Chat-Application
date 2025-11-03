from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, UploadFile, File
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os

from core.database import get_db
from model.chat_model import ChatMessageModel
from model.auth_model import User
from utils.websocket_manager import manager

router = APIRouter()

# === Uploads Folder ===
UPLOAD_DIR = "uploads/images"
os.makedirs(UPLOAD_DIR, exist_ok=True)



@router.post("/upload-image")
async def upload_image(file: UploadFile = File(...)):
    try:
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{file.filename}"
        file_path = os.path.join(UPLOAD_DIR, filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())

        file_url = f"/uploads/images/{filename}"
        return {"success": True, "url": file_url}
    except Exception as e:
        return JSONResponse(content={"success": False, "error": str(e)}, status_code=500)


@router.websocket("/ws/{sender}/{receiver}")
async def chat_websocket(websocket: WebSocket, sender: str, receiver: str, db: Session = Depends(get_db)):
    await manager.connect(sender, websocket)
    await manager.set_active_chat(sender, receiver)

    try:
        while True:
            data = await websocket.receive_json()
            message_text = data.get("message")
            content_type = data.get("content_type", "text")

            sender_user = db.query(User).filter(User.username == sender).first()
            receiver_user = db.query(User).filter(User.username == receiver).first()
            if not sender_user or not receiver_user:
                continue

            # Save message
            new_msg = ChatMessageModel(
                sender_id=sender_user.id,
                receiver_id=receiver_user.id,
                content=message_text,
                content_type=content_type,
                timestamp=datetime.now()
            )
            db.add(new_msg)
            db.commit()

            msg_data = {
                "type": "chat",
                "sender": sender,
                "receiver": receiver,
                "message": message_text,
                "content_type": content_type,
                "timestamp": str(new_msg.timestamp)
            }


            await manager.send_personal_message(msg_data, sender, receiver)
            await manager.send_notification_if_not_active(receiver, msg_data)

    except WebSocketDisconnect:
        await manager.disconnect(sender, websocket)
        await manager.set_active_chat(sender, None)
        print(f"❌ {sender} disconnected from chat with {receiver}")


@router.websocket("/ws/notify/{username}")
async def notify_websocket(websocket: WebSocket, username: str):
    await manager.connect(username, websocket)
    await manager.set_active_chat(username, None)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        await manager.disconnect(username, websocket)
        await manager.set_active_chat(username, None)
        print(f"🔕 {username} notification socket disconnected.")


@router.get("/messages/{sender}/{receiver}")
def get_chat_history(sender: str, receiver: str, db: Session = Depends(get_db)):
    sender_user = db.query(User).filter(User.username == sender).first()
    receiver_user = db.query(User).filter(User.username == receiver).first()
    if not sender_user or not receiver_user:
        return []

    msgs = (
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
            "content_type": m.content_type,
            "timestamp": m.timestamp
        }
        for m in msgs
    ]
