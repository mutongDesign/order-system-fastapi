from typing import List

from fastapi import APIRouter, WebSocket, HTTPException

import jwt
from core.security import jwt_token_key



class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, websocket: WebSocket, message: str):
        for connection in self.active_connections:
            await connection.send_text(message)

manager=ConnectionManager()

async def websocket_designer_login(websocket: WebSocket):
    await manager.connect(websocket)
    while True:
        data = await websocket.receive_text()
        try:
            print(websocket.query_params["token"])
            jwt.decode(websocket.query_params["token"], key=jwt_token_key ,algorithms=["HS256"])
            user_id=websocket.query_params["userid"]
            await manager.broadcast(websocket, user_id)
        except jwt.InvalidTokenError as e:
            await websocket.send_text(f"Message text was: 你没有权限")
            raise HTTPException(status_code=401,)