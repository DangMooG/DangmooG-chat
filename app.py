from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_socketio import SocketManager

from router import websocket_router

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

chat_app.include_router(websocket_router.router)

