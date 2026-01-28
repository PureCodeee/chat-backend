from typing import Dict, List
from fastapi import WebSocket


class ConnectionManager:
    def __init__(self):
        # chat_id -> list of websockets
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, chat_id: int, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.setdefault(chat_id, []).append(websocket)

    def disconnect(self, chat_id: int, websocket: WebSocket):
        conns = self.active_connections.get(chat_id)
        if not conns:
            return
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            del self.active_connections[chat_id]


    async def broadcast(self, chat_id: int, message: dict):
        for ws in self.active_connections.get(chat_id, []):
            await ws.send_json(message)
