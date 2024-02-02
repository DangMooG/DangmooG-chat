from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_socketio import SocketManager
import socketio
from router.websocket_router import get_current_user
from schema.message_schema import Message as Message_schema
from model.message_dbmodel import Room, Message
from core.utils import get_crud

chat_app = FastAPI(title="DangmooG", debug=True)
sm = SocketManager(app=chat_app, logger=True, engineio_logger=True)

# CORS RULES
origins = [
    "*"
]

chat_app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@chat_app.get("/")
async def root():
    return {"message": "당무지의 채팅서버입니다."}


class MyCustomNamespace(socketio.AsyncNamespace):
    def __init__(self, namespace):
        super().__init__(namespace=namespace)
        self.connected_users = set()
        self.room_users = {}
        self.crud_generator = get_crud()

    async def on_connect(self, sid, environ, auth):
        uid = await get_current_user(auth['token'])
        self.connected_users.add(uid)
        await sm.save_session(sid, {'uid': uid})

    async def on_disconnect(self, sid):
        session = sm.get_session(sid)
        self.connected_users.remove(session['uid'])
        await sm.disconnect(sid)

    async def on_begin_chat(self, sid, room: str):
        self.room_users.setdefault(room, set()).add(sid)
        await sm.enter_room(sid, room)

    async def on_exit_chat(self, sid, room: str):
        if sid in self.room_users.get(room, set()):
            self.room_users[room].remove(sid)
        await sm.leave_room(sid, room)

    async def on_send_chat(self, sid, data: dict):
        session = await sm.get_session(sid)
        sender = session['uid']
        crud = next(self.crud_generator)
        room_information = crud.search_record(Room, {"room_id": data["room"]})[0]
        print(room_information.buyer_id, "<-buyer, sender->", sender)
        print(f"room: {data['room']} message: {data['content']}")
        if len(self.room_users.get(data['room'], set())) < 2:
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
        crud.create_record(Message, Message_schema(
            room_id=data['room'],
            is_from_buyer=is_from_buyer,
            content=data["content"],
            read=0
        ))
        await self.send(data=data['content'], room=data['room'])
# content -> type: img, text, if img: list 형식으로  추가적인 dict 형식으로 받기

sm._sio.register_namespace(MyCustomNamespace('/'))
