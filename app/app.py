import os

from fastapi import FastAPI

from .config import settings
from .routes import auth, posts, chats, image, profile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from .db import engine, Base
import asyncio

app = FastAPI(title="FastAPI Session")

os.makedirs(settings.upload_dir, exist_ok=True)

# Указываем, с каких источников разрешены запросы
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://example.com",    # продакшн-домен
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # разрешённые источники
    allow_credentials=True,         # разрешаем куки / авторизацию
    allow_methods=["*"],            # разрешаем все HTTP-методы (GET, POST и т.д.)
    allow_headers=["*"],            # разрешаем все заголовки
)

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")

app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(chats.router)
app.include_router(image.router)
app.include_router(profile.router)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    return {"message": "Hello World"}
