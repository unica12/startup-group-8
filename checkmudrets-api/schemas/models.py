"""Pydantic-схемы для запросов и ответов API."""
from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


# ─── Auth ────────────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    device_id: str = Field(..., description="Уникальный идентификатор устройства")
    name: Optional[str] = Field(None, description="Имя пользователя")


class UserResponse(BaseModel):
    user_id: int
    device_id: str
    name: Optional[str]
    created_at: datetime

    model_config = {"from_attributes": True}


# ─── Items / Receipts ─────────────────────────────────────────────────────────

class ItemResponse(BaseModel):
    id: int
    name: str
    quantity: float
    price: float
    total: float
    category: str

    model_config = {"from_attributes": True}


class ReceiptResponse(BaseModel):
    id: int
    store_name: Optional[str]
    date: Optional[date]
    total: float
    items: List[ItemResponse] = []
    created_at: datetime

    model_config = {"from_attributes": True}


class UploadReceiptResponse(BaseModel):
    success: bool
    receipt: Optional[ReceiptResponse] = None
    mini_advice: Optional[str] = None
    error: Optional[str] = None


class ReceiptsListResponse(BaseModel):
    receipts: List[ReceiptResponse]
    total_count: int


# ─── Stats ────────────────────────────────────────────────────────────────────

class CategoryStat(BaseModel):
    category: str
    amount: float
    percent: int
    emoji: str


class LargestPurchase(BaseModel):
    name: str
    amount: float
    category: str


class StatsResponse(BaseModel):
    month: str  # "2026-04"
    total_spent: float
    receipts_count: int
    average_receipt: float
    by_category: List[CategoryStat]
    largest_purchase: Optional[LargestPurchase] = None


# ─── Advice ───────────────────────────────────────────────────────────────────

class AdviceResponse(BaseModel):
    advice: str
    generated_at: datetime


# ─── Report ───────────────────────────────────────────────────────────────────

class ReportPeriod(BaseModel):
    start: Optional[str]
    end: Optional[str]
    label: str


class TopCategory(BaseModel):
    category: str
    amount: float
    emoji: str


class ReportResponse(BaseModel):
    period: ReportPeriod
    total_spent: float
    receipts_count: int
    change_pct: float
    change_text: str
    top_categories: List[TopCategory]
    summary_text: str
