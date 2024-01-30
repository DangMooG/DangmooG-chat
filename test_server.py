from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_socketio import SocketManager
import socketio
from router.websocket_router import get_current_user
from dotenv import load_dotenv
chat_app = FastAPI(title="DangmooG", debug=True)
sm = SocketManager(app=chat_app, logger=True, engineio_logger=True)
load_dotenv()
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

    def on_connect(self, sid, environ, auth):
        uid = get_current_user(auth['token'])
        self.connected_users.add(uid)
        print(uid)
        sm.save_session(sid, {'uid': uid})

    def on_disconnect(self, sid):
        session = sm.get_session(sid)
        self.connected_users.remove(session['uid'])
        sm.disconnect(sid)

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
        print(f"room: {room} message: {content}")
        await self.send(data=content, room=room)


sm._sio.register_namespace(MyCustomNamespace('/chat'))


