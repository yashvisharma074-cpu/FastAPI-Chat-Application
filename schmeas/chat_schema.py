from pydantic import BaseModel
from pydantic import BaseModel

class ChatMessage(BaseModel):
    sender_id: int
    receiver_id: int
    content: str
