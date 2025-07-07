from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import os
from app.conf.settings import settings
from app.api.ws import ws_router
from app.api.routers import api_router
from app.database.mongo.session import db_lifespan
from app.pages import page_routes
import warnings

warnings.filterwarnings("ignore")

app = FastAPI(title="Auth Service", version="1.0.0", lifespan=db_lifespan)

for folder in ['app/static', 'app/templates']:
    os.makedirs(folder, exist_ok=True)

templates = Jinja2Templates(directory="templates")
app.mount('/static', StaticFiles(directory='app/static'), name='static')

app.add_middleware(
    CORSMiddleware, allow_origins=settings.ALLOWED_ORIGIN, 
    allow_credentials=True, allow_methods=["*"], allow_headers=["*"],)


app.include_router(
    api_router,
    prefix='/api'
)

app.include_router(
    ws_router,
    prefix='/ws',
)

app.include_router(
    page_routes,
)