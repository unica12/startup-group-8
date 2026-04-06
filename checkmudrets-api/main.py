"""Точка входа FastAPI-приложения ЧекМудрец."""
from __future__ import annotations

import logging

import uvicorn
from fastapi import FastAPI
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

# Инициализация приложения
app = FastAPI(
    title="ЧекМудрец API",
    description="REST API для мобильного приложения ЧекМудрец — сканирование чеков и анализ расходов",
    version="1.0.0",
)

# CORS — открываем для всех origins (MVP)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение роутеров
app.include_router(auth.router)
app.include_router(receipts.router)
app.include_router(stats.router)
app.include_router(advice.router)
app.include_router(report.router)


@app.on_event("startup")
async def on_startup() -> None:
    """При запуске: проверить конфиг и инициализировать БД."""
    validate_config()
    await init_db()
    logger.info("ЧекМудрец API запущен")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    """При остановке: закрыть соединения с БД."""
    await close_db()
    logger.info("ЧекМудрец API остановлен")


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
