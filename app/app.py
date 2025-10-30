from fastapi import FastAPI
from .routes import auth, posts, chats
from fastapi.middleware.cors import CORSMiddleware
from .db import engine, Base
import asyncio

app = FastAPI(title="FastAPI Session")

# Указываем, с каких источников разрешены запросы
origins = [
    "http://localhost:5173",  # React dev server
    "http://127.0.0.1:3000",
    "https://example.com",    # продакшн-домен
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,          # разрешённые источники
    allow_credentials=True,         # разрешаем куки / авторизацию
    allow_methods=["*"],            # разрешаем все HTTP-методы (GET, POST и т.д.)
    allow_headers=["*"],            # разрешаем все заголовки
)

app.include_router(auth.router)
app.include_router(posts.router)
app.include_router(chats.router)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    return {"message": "Hello World"}
