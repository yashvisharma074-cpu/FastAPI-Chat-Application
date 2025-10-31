from typing import Dict, Optional
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.active_chats: Dict[str, Optional[str]] = {}

    async def connect(self, username: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[username] = websocket
        self.active_chats[username] = None
        print(f"✅ {username} connected. Active users: {list(self.active_connections.keys())}")

    def disconnect(self, username: str):
        if username in self.active_connections:
            del self.active_connections[username]
        if username in self.active_chats:
            del self.active_chats[username]
        print(f"❌ {username} disconnected.")

    async def set_active_chat(self, username: str, chatting_with: Optional[str]):
        self.active_chats[username] = chatting_with
        print(f"💬 {username} is now chatting with {chatting_with}")

    async def send_personal_message(self, message: dict, sender: str, receiver: str):
        sender_ws = self.active_connections.get(sender)
        receiver_ws = self.active_connections.get(receiver)

        if sender_ws:
            await sender_ws.send_json(message)

        if receiver_ws:
            current_chat = self.active_chats.get(receiver)
            if current_chat == sender:
                await receiver_ws.send_json(message)
                print(f"📨 Message delivered from {sender} → {receiver}")
            else:
                notification = {
                    "type": "notification",
                    "from": sender,
                    "message": f"💬 New message from {sender}!",
                }
                await receiver_ws.send_json(notification)
                print(f"🔔 {receiver} chatting with {current_chat} → sent notification from {sender}")
        else:
            print(f"⚠️ Receiver {receiver} is offline. Message saved in DB only.")

    async def send_notification_if_not_active(self, receiver: str, message: dict):
        """Send notification if receiver is not chatting with sender."""
        receiver_ws = self.active_connections.get(receiver)
        current_chat = self.active_chats.get(receiver)

        if receiver_ws and current_chat != message.get("sender"):
            notification = {
                "type": "notification",
                "from": message["sender"],
                "message": f"💬 New message from {message['sender']}!"
            }
            await receiver_ws.send_json(notification)
            print(f"🔔 Notification sent to {receiver}")

    async def broadcast_user_list(self):
        user_list = list(self.active_connections.keys())
        for ws in self.active_connections.values():
            await ws.send_json({"type": "user_list", "users": user_list})


manager = ConnectionManager()
