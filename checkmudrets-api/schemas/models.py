"""Pydantic-схемы для запросов и ответов API."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal
from typing import List, Literal, Optional
from unicodedata import category
from uuid import UUID

from pydantic import BaseModel, Field, field_validator

from schemas.receipt_input import ReceiptInput, ReceiptWarning


# ─── Auth ────────────────────────────────────────────────────────────────────

class UserResponse(BaseModel):
    id: int
    name: Optional[str]
    email: Optional[str]
    created_at: datetime
    consents_complete: bool


class ConsentRequest(BaseModel):
    consents: dict[str, str] = Field(min_length=1, max_length=10)


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=50)

    @field_validator("name", mode="before")
    @classmethod
    def normalize_name(cls, value):
        if isinstance(value, str):
            value = " ".join(value.split())
            if any(category(char).startswith("C") for char in value):
                raise ValueError("Имя содержит недопустимые символы.")
        return value


class ProfileStats(BaseModel):
    receipts_count: int
    total_spent: Decimal
    items_count: int
    top_category: str | None


# ─── Items / Receipts ─────────────────────────────────────────────────────────

class ItemResponse(BaseModel):
    id: int
    name: str
    raw_name: str | None
    brand: str | None
    quantity: float | None
    unit: str | None
    price: float | None
    discount: float | None
    total: float
    category: str
    package_size: float | None
    package_unit: str | None

    model_config = {"from_attributes": True}


class ReceiptResponse(BaseModel):
    id: int
    store_name: Optional[str]
    date: Optional[date]
    total: float
    discount: float | None
    items: List[ItemResponse] = Field(default_factory=list)
    created_at: datetime

    model_config = {"from_attributes": True}


class RecognizeReceiptResponse(BaseModel):
    success: bool
    draft_id: UUID | None = None
    receipt: ReceiptInput | None = None
    warnings: list[ReceiptWarning] = Field(default_factory=list)
    retried: bool = False
    categories: list[str] = Field(default_factory=list)
    error: Optional[str] = None


class ReceiptsListResponse(BaseModel):
    receipts: List[ReceiptResponse]
    total_count: int


class ExportConsent(BaseModel):
    consent_type: str
    document_version: str
    accepted_at: datetime
    ip_address: str | None
    user_agent: str | None

    model_config = {"from_attributes": True}


class ExportReceipt(ReceiptResponse):
    raw_text: str | None


class AccountExport(BaseModel):
    profile: UserResponse
    receipts: list[ExportReceipt]
    consents: list[ExportConsent]
    exported_at: datetime


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

class InsightMetric(BaseModel):
    value: Decimal
    unit: str
    label: str


class Insight(BaseModel):
    type: Literal["store_comparison", "price_change", "unit_price", "shopping_frequency", "category_change",
                  "growth_driver", "forecast", "savings"]
    title: str
    observation: str
    recommendation: str
    metric: InsightMetric
    estimated_savings: Decimal | None = None
    evidence: list[str]
    confidence: Literal["medium", "high"]


class AdviceResponse(BaseModel):
    insights: list[Insight]
    empty_message: str | None = None
    generated_at: datetime


class SavedReceiptResponse(BaseModel):
    receipt: ReceiptResponse
    mini_advice: Insight | None = None


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
    change_pct: float | None
    change_text: str
    top_categories: List[TopCategory]
    summary_text: str
