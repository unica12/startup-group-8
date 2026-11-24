"""Входные данные распознавания и подтверждения чека."""
from datetime import date as Date
from decimal import Decimal
import re
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

Unit = Literal["шт", "кг", "г", "л", "мл"]
PackageUnit = Literal["кг", "г", "л", "мл"]
Money = Annotated[Decimal, Field(ge=0, le=Decimal("1000000000"), decimal_places=2)]
UnitPrice = Annotated[Decimal, Field(ge=0, le=Decimal("1000000000"), decimal_places=4)]
Quantity = Annotated[Decimal, Field(gt=0, le=Decimal("10000000"), decimal_places=6)]
Name = Annotated[str, Field(max_length=256)]


class ReceiptLine(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    raw_name: Name | None = None
    name: Name | None = None
    brand: Annotated[str, Field(max_length=128)] | None = None
    quantity: Quantity | None = None
    unit: Unit | None = None
    price: UnitPrice | None = None
    discount: Money | None = None
    total: Money | None = None
    category: Annotated[str, Field(max_length=64)] | None = None
    package_size: Quantity | None = None
    package_unit: PackageUnit | None = None

    @field_validator("raw_name", "name", "brand", "category", mode="before")
    @classmethod
    def safe_text(cls, value):
        if isinstance(value, str) and "\x00" in value:
            raise ValueError("Недопустимый символ")
        return value


class ReceiptInput(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    store_name: Name | None = None
    date: Date | None = None
    total: Money | None = None
    discount: Money | None = None
    items: list[ReceiptLine] = Field(max_length=120)

    @field_validator("date", mode="before")
    @classmethod
    def iso_date(cls, value):
        if value is None or type(value) is Date or isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}", value):
            return value
        raise ValueError("Дата должна быть в формате YYYY-MM-DD")

    @field_validator("store_name", mode="before")
    @classmethod
    def safe_store_name(cls, value):
        return ReceiptLine.safe_text(value)


class ConfirmReceipt(BaseModel):
    receipt: ReceiptInput
    accept_warnings: bool = False


class ReceiptWarning(BaseModel):
    message: str
    item: int | None = None
    blocking: bool = False
    retry: bool = False
