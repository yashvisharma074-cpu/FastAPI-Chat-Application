from typing import Dict, Optional
from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # username → websocket
        self.active_connections: Dict[str, WebSocket] = {}
        # username → currently open chat with whom
        self.active_chats: Dict[str, Optional[str]] = {}

    async def connect(self, username: str, websocket: WebSocket):
        """Accept connection and store it by username"""
        await websocket.accept()
        self.active_connections[username] = websocket
        self.active_chats[username] = None  # no chat open initially
        print(f"✅ {username} connected. Active users: {list(self.active_connections.keys())}")

    def disconnect(self, username: str):
        """Remove user connection when disconnected"""
        if username in self.active_connections:
            del self.active_connections[username]
        if username in self.active_chats:
            del self.active_chats[username]
        print(f"❌ {username} disconnected.")

    async def set_active_chat(self, username: str, chatting_with: Optional[str]):
        """Track which user someone is currently chatting with"""
        self.active_chats[username] = chatting_with
        print(f"💬 {username} is now chatting with {chatting_with}")

    async def send_personal_message(self, message: dict, sender: str, receiver: str):
        """
        Send message to both sender & receiver if connected.
        If receiver not actively chatting with sender, send 'notification' type message.
        """
        receiver_ws = self.active_connections.get(receiver)
        sender_ws = self.active_connections.get(sender)

        # Always send message to sender (so they see it instantly)
        if sender_ws:
            await sender_ws.send_json(message)

        if receiver_ws:
            # Send message to receiver
            await receiver_ws.send_json(message)

            # If receiver not chatting with sender → send notification
            if self.active_chats.get(receiver) != sender:
                notification = {
                    "type": "notification",
                    "from": sender,
                    "message": "New message received!",
                }
                await receiver_ws.send_json(notification)

# ✅ Single global instance
manager = ConnectionManager()
