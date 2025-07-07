from fastapi import APIRouter
from .chat_websocket import router

ws_router = APIRouter()

ws_router.include_router(
    router,
    prefix='',
)