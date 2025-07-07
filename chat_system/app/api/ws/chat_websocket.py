import json
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.api.managers.redis_manager import RedisPubSub
from app.api.managers.websocket_manager import WebsocketManager
from app.database.mongo.models import *

router = APIRouter()
manager = WebsocketManager()
redis_pubsub = RedisPubSub()


async def handle_read_receipt(message_id: str, user_id: str, group_id: str = None):
    message = await Message.get(message_id)
    if user_id not in message.read_by:
        message.read_by.append(user_id)
        await message.save()
        
        # Notify sender about read status
        if not group_id:
            await redis_pubsub.publish(
                f"user:{message.sender_id}",
                {
                    "type": "read_update",
                    "message_id": message_id,
                    "reader_id": user_id
                }
            )
        else:
            # For group chats, notify all members
            group = await Group.get(group_id)
            for member_id in group.members:
                if member_id != user_id:
                    await redis_pubsub.publish(
                        f"user:{member_id}",
                        {
                            "type": "group_read_update",
                            "message_id": message_id,
                            "reader_id": user_id,
                            "group_id": group_id
                        }
                    )
                    

@router.websocket('/{user_id}')
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    pubsub = await redis_pubsub.subscribe(f"user:{user_id}")
    try:
        while True:
            # Listen for Redis messages
            redis_msg = await pubsub.get_message(ignore_subscribe_messages=True)
            if redis_msg:
                await websocket.send_json(json.loads(redis_msg['data']))
            
            # Handle WebSocket messages
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            if message_data['type'] == 'read_receipt':
                await handle_read_receipt(
                    message_data['message_id'],
                    user_id,
                    message_data.get('group_id')
                )
                
    except WebSocketDisconnect:
        manager.disconnect(user_id)
        await redis_pubsub.unsubscribe(f"user:{user_id}")