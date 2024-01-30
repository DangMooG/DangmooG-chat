from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_socketio import SocketManager
import socketio
from router.websocket_router import get_current_user
from schema.message_schema import Message as Message_schema
from model.message_dbmodel import Room, Message
from core.utils import get_crud

chat_app = FastAPI(title="DangmooG", debug=True)
socket_manager = SocketManager(app=chat_app, logger=True, engineio_logger=True)

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

with socket_manager as sm:
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

