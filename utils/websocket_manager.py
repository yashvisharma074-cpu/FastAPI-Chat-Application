from typing import Dict, List, Optional
from fastapi import WebSocket
from asyncio import Lock


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, List[WebSocket]] = {}
        self.active_chats: Dict[str, Optional[str]] = {}
        self.lock = Lock()


    async def connect(self, username: str, websocket: WebSocket):
        """Register new websocket connection for a user"""
        await websocket.accept()
        async with self.lock:
            self.active_connections.setdefault(username, []).append(websocket)
            self.active_chats.setdefault(username, None)
        print(f"✅ {username} connected ({len(self.active_connections[username])} tabs)")

    async def disconnect(self, username: str, websocket: WebSocket):
        """Remove websocket connection on disconnect"""
        async with self.lock:
            if username in self.active_connections:
                if websocket in self.active_connections[username]:
                    self.active_connections[username].remove(websocket)
                    print(f"❌ {username} disconnected one socket.")
                if not self.active_connections[username]:
                    del self.active_connections[username]
                    self.active_chats.pop(username, None)
                    print(f"🧹 {username} fully offline.")
        print(f"👥 Active users: {list(self.active_connections.keys())}")

    async def set_active_chat(self, username: str, chatting_with: Optional[str]):
        """Track who a user is currently chatting with"""
        self.active_chats[username] = chatting_with
        print(f"💬 {username} is now chatting with {chatting_with}")

 
    async def send_personal_message(self, message: dict, sender: str, receiver: str):
        """Send message only between sender and receiver"""
        try:
            sender_ws_list = self.active_connections.get(sender, [])
            receiver_ws_list = self.active_connections.get(receiver, [])

            for ws in sender_ws_list + receiver_ws_list:
                if ws.application_state.name != "DISCONNECTED":
                    await ws.send_json(message)

        except Exception as e:
            print(f"⚠️ Error sending message {sender} → {receiver}: {e}")


    async def send_notification_if_not_active(self, receiver: str, message: dict):
        """Send notification only if receiver is not chatting with sender"""
        receiver_conns = self.active_connections.get(receiver, [])
        current_chat = self.active_chats.get(receiver)

        if receiver_conns and current_chat != message.get("sender"):
            notification = {
                "type": "notification",
                "from": message["sender"],
                "message": f"💬 New message from {message['sender']}"
            }
            for ws in receiver_conns:
                try:
                    if ws.application_state.name != "DISCONNECTED":
                        await ws.send_json(notification)
                except:
                    pass
            print(f"🔔 Notification sent to {receiver}")

    async def broadcast_user_list(self):
        """Send list of all active users to everyone"""
        user_list = list(self.active_connections.keys())
        payload = {"type": "user_list", "users": user_list}

        for user, sockets in self.active_connections.items():
            for ws in sockets:
                try:
                    if ws.application_state.name != "DISCONNECTED":
                        await ws.send_json(payload)
                except:
                    pass
        print("📢 Broadcasted updated user list.")


# Singleton instance
manager = ConnectionManager()
