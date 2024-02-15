from pydantic import BaseModel


class Message(BaseModel):
    room_id: str
    is_from_buyer: int
    is_photo: int
    content: str
    read: int