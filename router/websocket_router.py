import os
from datetime import datetime

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from jose import jwt, JWTError
from starlette import status

from schema.message_schema import Message as Message_schema
from typing import Dict
from core.utils import get_crud
# from pyfcm import FCMNotification

from model.message_dbmodel import Room, Message

router = APIRouter()


# Your api-key can be gotten from:  https://console.firebase.google.com/project/<project-name>/settings/cloudmessaging
# push_service = FCMNotification(api_key=os.environ.get("FCM_API_KEY"))
# DB에 따로 FCM 토큰을 저장하고 상대방이 접속중이 아닐 때는 DB에서 토큰을 받아와서 해당 사용자에게 푸시알림 실행하는 과정 시행


class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[int, WebSocket] = {}

    async def connect(self, websocket: WebSocket, user: int):
        await websocket.accept()
        self.active_connections[user] = websocket

    def disconnect(self, user: int):
        if user in self.active_connections:
            del self.active_connections[user]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, room: str, sender: int):
        crud_generator = get_crud()
        crud = next(crud_generator)
        room_information = crud.search_record(Room, {"room_id": room})[0]
        print(room_information.buyer_id, "<-buyer, sender->", sender)
        print(f"room: {room} message: {message}")
        if room_information.buyer_id == sender:
            if room_information.seller_id not in self.active_connections.keys():
                crud.create_record(Message, Message_schema(
                    room_id=room,
                    is_from_buyer=1,
                    content=message,
                    read=0
                ))
                print("There is no opponent, app-push function will be executed")
            else:
                crud.create_record(Message, Message_schema(
                    room_id=room,
                    is_from_buyer=1,
                    content=message,
                    read=1
                ))
                await self.active_connections[room_information.seller_id].send_text(room+message)

        else:
            if room_information.buyer_id not in self.active_connections.keys():
                crud.create_record(Message, Message_schema(
                    room_id=room,
                    is_from_buyer=0,
                    content=message,
                    read=0
                ))
                print("There is no opponent, app-push function will be executed")
            else:
                crud.create_record(Message, Message_schema(
                    room_id=room,
                    is_from_buyer=0,
                    content=message,
                    read=1
                ))
                await self.active_connections[room_information.buyer_id].send_text(room+message)


manager = ConnectionManager()
SECRET_KEY = os.environ["ACCESS_TOKEN_HASH"]
ALGORITHM = "HS256"


def get_current_user(token: str):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        account_id: str = payload.get("sub")
        if datetime.fromtimestamp(payload.get("exp")) < datetime.utcnow():
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if account_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    else:
        return account_id


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, token: str):
    user_id = int(get_current_user(token))
    print(f"userid: {user_id}")
    await manager.connect(websocket, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            room_name = data[:36]
            message = data[36:]
            # database에 채팅에 대한 내용 올리는 거 추가
            # 나중에 기존 api 서버에서 채팅 내역을 조회할 수 있는 api 가져오기
            await manager.broadcast(message, room_name, user_id)
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        # await manager.broadcast(f"Client left the chat room: {room_name}", room_name)
