from fastapi import FastAPI
from .routes import auth
from .db import engine, Base
import asyncio

app = FastAPI(title="FastAPI Session")

app.include_router(auth.router)

@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@app.get("/")
async def root():
    return {"message": "Hello World"}
