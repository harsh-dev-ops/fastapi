import redis.asyncio as redis
import json
from app.conf.settings import settings

class RedisPubSub:
    def __init__(self):
        self.redis = redis.Redis(
            host=settings.REDIS_HOST, 
            port=settings.REDIS_PORT, 
            db=settings.REDIS_DB
            )
        self.pubsub = self.redis.pubsub()

    async def publish(self, channel, message):
        await self.redis.publish(channel, json.dumps(message))

    async def subscribe(self, channel):
        await self.pubsub.subscribe(channel)
        return self.pubsub

    async def unsubscribe(self, channel):
        await self.pubsub.unsubscribe(channel)