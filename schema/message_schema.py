from pydantic import BaseModel


class Message(BaseModel):
    room_id: str
    is_from_buyer: int
    content: str