from fastapi import FastAPI
from motor.motor_asyncio import AsyncIOMotorClient
from beanie import init_beanie
from contextlib import asynccontextmanager
from logging import info
from app.conf.settings import settings
from app.database.mongo.models import User, Message, Group


document_models = [
    User,
    Message, 
    Group
    ]


@asynccontextmanager
async def db_lifespan(app: FastAPI):
    
    app.mongo_client = AsyncIOMotorClient(settings.MONGO_URL)
    app.database = app.mongo_client.get_default_database()
    await init_beanie(app.database, document_models=document_models)
    ping_response = await app.database.command("ping")
    if int(ping_response["ok"]) != 1:
        raise Exception("Problem connecting to database cluster.")
    else:
        info("Connected to database cluster.")
    yield
    
    app.mongo_client.close()
    
    
async def init_db():
    client = AsyncIOMotorClient(settings.MONGO_URL)
    await init_beanie(
        database=client.get_default_database(),
        document_models=document_models
    )
