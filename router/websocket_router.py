import os
from datetime import datetime

import socketio
from fastapi import APIRouter, HTTPException
from jose import jwt, JWTError
from starlette import status

from schema.message_schema import Message as Message_schema
from core.utils import get_crud
# from pyfcm import FCMNotification

from model.message_dbmodel import Room, Message
from ..app import socket_manager as sm

router = APIRouter()


# Your api-key can be gotten from:  https://console.firebase.google.com/project/<project-name>/settings/cloudmessaging
# push_service = FCMNotification(api_key=os.environ.get("FCM_API_KEY"))
# DB에 따로 FCM 토큰을 저장하고 상대방이 접속중이 아닐 때는 DB에서 토큰을 받아와서 해당 사용자에게 푸시알림 실행하는 과정 시행


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
        return int(account_id)


class MyCustomNamespace(socketio.AsyncNamespace):
    def __init__(self, namespace):
        super().__init__(namespace=namespace)
        self.connected_users = set()
        self.room_users = {}
        crud_generator = get_crud()
        self.crud = next(crud_generator)

    async def on_connect(self, sid, token):
        uid = get_current_user(token)
        self.connected_users.add(uid)
        async with sm.session(sid) as session:
            session['uid'] = uid

    async def on_disconnect(self, sid, token):
        uid = get_current_user(token)
        self.connected_users.remove(uid)
        await sm.disconnect(sid)

    async def on_begin_chat(self, sid, room: str):
        self.room_users.setdefault(room, set()).add(sid)
        await sm.enter_room(sid, room)

    async def on_exit_chat(self, sid, room: str):
        if sid in self.room_users.get(room, set()):
            self.room_users[room].remove(sid)
        await sm.leave_room(sid, room)

    async def on_send_chat(self, sid, room, content):
        session = await sm.get_session(sid)
        sender = session['uid']
        room_information = self.crud.search_record(Room, {"room_id": room})[0]
        print(room_information.buyer_id, "<-buyer, sender->", sender)
        print(f"room: {room} message: {content}")
        if len(self.room_users.get(room, set())) < 2:
            not_in_room = True
        else:
            not_in_room = False
        if room_information.buyer_id == sender:
            is_from_buyer = 1
            if room_information.seller_id not in self.connected_users:
                print("app push", self.connected_users)
            elif not_in_room:
                print("in app push", self.room_users)
        else:
            is_from_buyer = 0
            if room_information.buyer_id not in self.connected_users:
                print("app push", self.connected_users)
            elif not_in_room:
                print("in app push", self.room_users)
        self.crud.create_record(Message, Message_schema(
            room_id=room,
            is_from_buyer=is_from_buyer,
            content=content["message"],
            read=0
        ))
        await self.send(data=content, room=room)


sm.register_namespace(MyCustomNamespace('/chat'))

