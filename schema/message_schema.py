from pydantic import BaseModel, Field


class Message(BaseModel):
    subject: str = Field(None, title="Target topic to publish")
    body: dict = Field(None, title="Content to be sent")