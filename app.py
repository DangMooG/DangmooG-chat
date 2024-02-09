from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_socketio import SocketManager
import socketio
from router.websocket_router import get_current_user
from schema.message_schema import Message as Message_schema
from model.message_dbmodel import Room, Message, Account
from core.utils import get_crud

import firebase_admin
from firebase_admin import credentials
from firebase_admin import messaging
from firebase_admin import auth
import json

chat_app = FastAPI(title="DangmooG", debug=True)
sm = SocketManager(app=chat_app, logger=True, engineio_logger=True)
credit = credentials.Certificate("firebase-adminsdk.json")
firebase_admin.initialize_app(credit)

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


async def send_push(token: str, title: str, body: str):
    message = messaging.Message(
        notification=messaging.Notification(
            title=title,
            body=body,
        ),
        token=token,
        android=messaging.AndroidConfig(
            priority='high',
            notification=messaging.AndroidNotification(
                sound='default'
            )
        ),
        apns=messaging.APNSConfig(
            payload=messaging.APNSPayload(
                aps=messaging.Aps(
                    sound='default'
                ),
            ),
        ),
    )
    # Response is a message ID string.
    try:
        response = messaging.send(message)
        print('Successfully sent message:', response)
    except messaging.exceptions.InvalidArgumentError:
        print("token not available")
        return -1
    except messaging.UnregisteredError:
        print("token not registered")
        return -1
    return 0


class MyCustomNamespace(socketio.AsyncNamespace):
    def __init__(self, namespace):
        super().__init__(namespace=namespace)
        self.connected_users = {}
        self.room_users = {}

    async def on_connect(self, sid, environ, auth):
        uid = await get_current_user(auth['token'])
        self.connected_users[uid] = sid
        await sm.save_session(sid, {'uid': uid})

    async def on_disconnect(self, sid):
        session = await sm.get_session(sid)
        del self.connected_users[session['uid']]
        await sm.disconnect(sid)

    async def on_begin_chat(self, sid, room: str):
        self.room_users.setdefault(room, set()).add(sid)
        await sm.enter_room(sid, room)

    async def on_exit_chat(self, sid, room: str):
        if sid in self.room_users.get(room, set()):
            self.room_users[room].remove(sid)
        await sm.leave_room(sid, room)

    # data = {type: img or txt, room: room_id, content: img format hint or chat content}
    async def on_send_chat(self, sid, data: dict):
        session = await sm.get_session(sid)
        sender = session['uid']
        crud_generator = get_crud()
        crud = next(crud_generator)
        room_information = crud.search_record(Room, {"room_id": data["room"]})[0]
        print(room_information.buyer_id, "<-buyer, sender->", sender)
        print(f"room: {data['room']} message: {data['content']}")
        if len(self.room_users.get(data['room'], set())) < 2:
            in_room = 0
        else:
            in_room = 1
        if room_information.buyer_id == sender:
            is_from_buyer = 1
            reciever = room_information.seller_id
            print(self.connected_users.keys(), self.connected_users.keys())
            if room_information.seller_id not in self.connected_users.keys():
                sender_account = crud.get_record(Account, {"account_id": sender})
                uname = sender_account.username
                reciever_obj: Account = crud.get_record(Account, {"account_id": reciever})
                body = json.dumps({"room": data['room'], "post_id": room_information.post_id, "type": data['type'], "message": data['content']})
                response = await send_push(reciever_obj.fcm, uname, body)
                if response == -1:
                    crud.patch_record(Account, {"fcm": None})
                print("app push", self.connected_users[sender])
            elif not in_room:
                print("in app push", self.room_users)
        else:
            is_from_buyer = 0
            reciever = room_information.buyer_id
            print(self.connected_users.keys(), self.connected_users.keys())
            if room_information.buyer_id not in self.connected_users.keys():
                sender_account = crud.get_record(Account, {"account_id": sender})
                uname = sender_account.username
                reciever_obj: Account = crud.get_record(Account, {"account_id": reciever})
                body = json.dumps({"room": data['room'], "post_id": room_information.post_id, "type": data['type'], "message": data['content']})
                response = await send_push(reciever_obj.fcm, uname, body)
                if response == -1:
                    crud.patch_record(Account, {"fcm": None})
                print("app push", self.connected_users)
            elif not in_room:
                print("in app push", self.room_users)
        if data['type'] == 'txt':
            crud.create_record(Message, Message_schema(
                room_id=data['room'],
                is_from_buyer=is_from_buyer,
                content=data["content"],
                read=in_room
            ))
        # await self.send(data=json.dumps({"type": data['type'], "content": data['content']}), room=data['room'])
        if reciever in self.connected_users.keys():
            await self.send(data={"room": data['room'], "type": data['type'], "content": data['content']}, to=self.connected_users[reciever], skip_sid=sid)
# content -> type: img, text, if img: list 형식으로  추가적인 dict 형식으로 받기

sm._sio.register_namespace(MyCustomNamespace('/'))
