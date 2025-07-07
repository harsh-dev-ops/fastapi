import asyncio
from fastapi.websockets import WebSocket

from app.database.mongo.models import *

class WebsocketManager:
    def __init__(self):
        self.active_connections: dict[str, WebSocket] = {}

    async def connect(self, user_id: str, websocket: WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket
        await User.get(user_id).update({"$set": {"online": True}})

    def disconnect(self, user_id: str):
        if user_id in self.active_connections:
            del self.active_connections[user_id]
        asyncio.create_task(User.get(user_id).update({"$set": {"online": False}}))

    async def send_personal_message(self, message: dict, user_id: str):
        if user_id in self.active_connections:
            await self.active_connections[user_id].send_json(message)