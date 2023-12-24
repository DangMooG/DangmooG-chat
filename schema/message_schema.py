from pydantic import BaseModel, Field


class Message(BaseModel):
    room_id: str
    is_from_buyer: int
    content: str