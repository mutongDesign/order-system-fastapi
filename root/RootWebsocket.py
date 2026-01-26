import json

from fastapi import FastAPI, WebSocket, HTTPException, Query
from sqlalchemy.orm import Session
from websockets.exceptions import ConnectionClosedOK,ConnectionClosedError
from starlette.websockets import WebSocketState, WebSocketDisconnect

from core.CreateEngine import engine
from core.security import jwt_token_key, oauth2_scheme

from designer.DesignerTableBase import DesignerRegisterTable

import jwt
import re


import logging
logger = logging.getLogger("uvicorn")

async def db_update_online_status(user_id, status):
    with Session(engine) as session, session.begin():
        query= session.query(DesignerRegisterTable).filter(DesignerRegisterTable.user_id==user_id)
        query.update({"on_line_status":status})

class ConnectionManager:
    def __init__(self):
        self.ws_to_user_connection:dict[WebSocket,str] = {}
        self.user_to_ws_connection:dict[str,list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.ws_to_user_connection[websocket] = ""

    # 将当前用户加入连接池
    async def register_user(self, websocket: WebSocket, user_id: str,role: str):

        if websocket in self.ws_to_user_connection:
            old_user_id = self.ws_to_user_connection[websocket]
            if old_user_id and old_user_id in self.user_to_ws_connection:
                if websocket in self.user_to_ws_connection[old_user_id]:
                    self.user_to_ws_connection[old_user_id].remove(websocket)
                if len(self.user_to_ws_connection[old_user_id]) == 0:
                    del self.user_to_ws_connection[old_user_id]

        self.ws_to_user_connection[websocket]=user_id

        if user_id not in self.user_to_ws_connection:
            self.user_to_ws_connection[user_id]=[]
        if websocket not in self.user_to_ws_connection[user_id]:
            self.user_to_ws_connection[user_id].append(websocket)

        await db_update_online_status(user_id, True)

        broadcast_msg={
            "type": "client_connection",
            "role":role,
            "user_id":user_id,
            "data":"online",
        }

        await self.online_status_broadcast(broadcast_msg)

    # 关闭链接并在连接池里清除当前用户
    async def disconnect(self, websocket: WebSocket):
        try:
            await websocket.close()
        except RuntimeError:
            pass

        if websocket not in self.ws_to_user_connection:
            return

        user_id = self.ws_to_user_connection[websocket]
        del self.ws_to_user_connection[websocket]

        if user_id in self.user_to_ws_connection:
            if websocket in self.user_to_ws_connection[user_id]:
                self.user_to_ws_connection[user_id].remove(websocket)
            if len(self.user_to_ws_connection[user_id]) == 0:
                del self.user_to_ws_connection[user_id]
                await db_update_online_status(user_id, False)

        broadcast_msg = {
            "type": "client_connection",
            "user_id": user_id,
            "data": "offline",
        }
        await self.online_status_broadcast(broadcast_msg)

    async def online_status_broadcast(self, broadcast_msg):
        for connection, uid in self.ws_to_user_connection.items():
            try:
                if connection.client_state == WebSocketState.CONNECTED:
                    await connection.send_text(json.dumps(broadcast_msg))
                else:
                    await self.disconnect(connection)

            # 专项捕获网络层异常 --------------------------
            except (ConnectionResetError, BrokenPipeError) as e:
                logger.warning(f" 连接中断: {connection.client}  | {str(e)}")
                await self.disconnect(connection)

            # 专项捕获协议层异常 --------------------------
            except (ConnectionClosedOK, ConnectionClosedError) as e:
                logger.info(f" 安全断开: {connection.client}  | 状态码:{e.code}")
                await self.disconnect(connection)

            # 兜底保护（范围收窄）-----------------------
            except RuntimeError as e:  # 特定于异步框架的运行时错误
                logger.error(f" 运行时异常: {type(e).__name__} | {str(e)}")
                await self.disconnect(connection)

            except Exception as e:
                logger.critical(f" 未预料的系统级异常: {type(e).__name__} - {str(e)}")
                await self.disconnect(connection)

    async def new_order_broadcast(self, user_id:str, message:dict):
        for websocket in self.user_to_ws_connection[user_id].copy():
            logger.info(f'22222222{user_id}{message}')
            try:
                if websocket.client_state == WebSocketState.CONNECTED:
                    logger.info(f'22222222{user_id}{message}')
                    await websocket.send_text(json.dumps(message))
                else:
                    logger.info(f'33333333333{user_id}{message}')
                    await self.disconnect(websocket)
            except (ConnectionResetError, BrokenPipeError) as e:
                logger.warning(f"给用户 {user_id} 发消息失败：{str(e)}")
                await self.disconnect(websocket)

manager=ConnectionManager()

async def watch_login_status(websocket: WebSocket):
    try:
        raw_token=websocket.query_params.get('token')
        token = re.sub(r"^Bearer\s+", "", raw_token, flags=re.I)
        if not token:
            await websocket.close(code=4000, reason="Missing token")
            return

        payload = jwt.decode(token, key=jwt_token_key, algorithms=["HS256"])

        logger.info(payload)

        user_id = payload.get("user_id")
        role = payload.get("role")

        # 新增：拦截token有但字段缺失的场景
        if not user_id or not role:
            logger.error(f"Token合法但缺少字段：user_id/role | payload: {payload}")
            await websocket.close(code=4002, reason="Missing user_id/role in token")
            return

    except jwt.PyJWTError as e:
        logger.error(f"JWT解析失败：{str(e)}")  # 加日志便于排查问题
        await websocket.close(code=4001, reason="Invalid token")
        return

    await manager.connect(websocket)
    try:
        while True:
            message = await websocket.receive_text()

            try:
                payload = json.loads(message)
            except json.JSONDecodeError as e:
                logger.error(f"非法JSON格式，原始消息：{message} | 错误：{str(e)}")
                continue  # 跳过非法消息，不中断循环

            if payload.get("type") == "clientConnection":
                await manager.register_user(websocket, user_id, role)

    except WebSocketDisconnect:
        logger.info("客户端主动断开")
    except (RuntimeError, ConnectionResetError) as e:
        logger.error(f" 网络异常：{str(e)}")
    except KeyError as e:
        logger.error(f" 协议字段缺失：{str(e)}")
    except Exception as e:
        logger.critical(f" 未处理异常：{type(e).__name__} - {str(e)}")
    finally:
        await manager.disconnect(websocket)






