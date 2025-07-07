from fastapi import APIRouter
from app.api.managers.redis_manager import RedisPubSub
from app.database.mongo.models import *


router = APIRouter()
redis_pubsub = RedisPubSub()


@router.post("/send/{receiver_id}")
async def send_message(sender_id: str, receiver_id: str, content: str, is_group: bool = False):
    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content,
        is_group=is_group
    )
    await message.insert()
    
    # Prepare message payload
    message_payload = {
        "type": "new_message",
        "message_id": str(message.id),
        "sender_id": sender_id,
        "content": content,
        "timestamp": message.timestamp.isoformat(),
        "is_group": is_group
    }
    
    # Publish to appropriate channels
    if is_group:
        group = await Group.get(receiver_id)
        for member_id in group.members:
            if member_id != sender_id:  # Don't send to self
                await redis_pubsub.publish(f"user:{member_id}", {
                    **message_payload,
                    "unread": True
                })
            else:
                await redis_pubsub.publish(f"user:{member_id}", {
                    **message_payload,
                    "unread": False
                })
    else:
        # 1:1 chat
        await redis_pubsub.publish(f"user:{receiver_id}", {
            **message_payload,
            "unread": True
        })
        # Also send to sender
        await redis_pubsub.publish(f"user:{sender_id}", {
            **message_payload,
            "unread": False
        })
    
    return {"status": "sent"}


@router.get("/unread-count/{user_id}")
async def get_unread_count(user_id: str):
    unread_messages = await Message.find(
        {"$and": [
            {"receiver_id": user_id},
            {"read_by": {"$nin": [user_id]}}
        ]}
    ).count()
    return {"count": unread_messages}