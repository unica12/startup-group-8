"""Точка входа FastAPI-приложения ЧекМудрец."""
from __future__ import annotations

import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from database.db import close_db, init_db
from routers import advice, auth, receipts, report, stats
from utils.config import HOST, PORT, validate_config

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI):
    validate_config()
    try:
        await init_db()
        logger.info("ЧекМудрец API запущен")
        yield
    finally:
        await close_db()
        logger.info("ЧекМудрец API остановлен")

# Инициализация приложения
app = FastAPI(
    title="ЧекМудрец API",
    description="REST API для мобильного приложения ЧекМудрец — сканирование чеков и анализ расходов",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — открываем для всех origins (MVP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def disable_response_caching(request: Request, call_next):
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    return response

# Подключение роутеров
app.include_router(auth.router)
app.include_router(receipts.router)
app.include_router(stats.router)
app.include_router(advice.router)
app.include_router(report.router)


@app.get("/", tags=["health"])
async def root() -> dict:
    """Проверка работоспособности API."""
    return {"status": "ok", "service": "ЧекМудрец API", "version": "1.0.0"}


@app.get("/health", tags=["health"])
async def health() -> dict:
    """Health check для мониторинга."""
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
