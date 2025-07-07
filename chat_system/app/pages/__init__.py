from fastapi import APIRouter
from .home_page import router


page_routes = APIRouter()

page_routes.include_router(
    router, 
    prefix=''
    )