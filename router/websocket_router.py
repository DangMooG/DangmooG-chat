import os
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from schema.message_schema import Message
from typing import Dict
from pyfcm import FCMNotification

router = APIRouter()

# Your api-key can be gotten from:  https://console.firebase.google.com/project/<project-name>/settings/cloudmessaging
# push_service = FCMNotification(api_key=os.environ.get("FCM_API_KEY"))
# DB에 따로 FCM 토큰을 저장하고 상대방이 접속중이 아닐 때는 DB에서 토큰을 받아와서 해당 사용자에게 푸시알림 실행하는 과정 시행

class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Dict[int, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room: str, user: int):
        await websocket.accept()
        if room in self.active_connections.keys():
            self.active_connections[room][user] = websocket
        else:
            self.active_connections[room] = {user: websocket}

    def disconnect(self, room: str, user: int):
        del self.active_connections[room][user]

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, websocket: WebSocket, message: str, room: str):
        if len(self.active_connections[room]) < 2:
            print("There is no opponent, app-push function will be executed")
            # FCM message gogogogo

        for connection in self.active_connections[room].values():
            if connection is websocket:  # pass if the connection is mine
                continue
            await connection.send_text(message)


manager = ConnectionManager()


@router.websocket("/chatting/{room_name}/{user_id}")
async def websocket_endpoint(websocket: WebSocket, room_name: str, user_id: int):  # 나중에 get current user 해야함
    await manager.connect(websocket, room_name, user_id)
    try:
        while True:
            data = await websocket.receive_text()
            # database에 채팅에 대한 내용 올리는 거 추가
            # 나중에 기존 api 서버에서 채팅 내역을 조회할 수 있는 api 가져오기
            await manager.broadcast(websocket, data, room_name)
    except WebSocketDisconnect:
        manager.disconnect(room_name, user_id)
        # await manager.broadcast(f"Client left the chat room: {room_name}", room_name)