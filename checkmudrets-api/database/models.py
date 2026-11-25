"""Модели базы данных SQLAlchemy для ЧекМудрец API."""
from __future__ import annotations

from sqlalchemy import (
    Boolean, Column, Date, DateTime, Float, ForeignKey,
    Integer, String, Text, UniqueConstraint, Uuid, func,
)
from sqlalchemy.orm import DeclarativeBase, relationship

from utils.receipt_dates import reporting_day


class Base(DeclarativeBase):
    pass


class User(Base):
    """Прикладной профиль пользователя Supabase Auth."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    auth_user_id = Column(Uuid, unique=True, index=True)
    name = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Связь с чеками
    receipts = relationship("Receipt", back_populates="user")


class AccountDeletion(Base):
    __tablename__ = "account_deletions"

    # После завершения остаётся только хеш UUID для блокировки ранее выданных JWT.
    id = Column(String(64), primary_key=True)
    auth_user_id = Column(Uuid, nullable=True)


class Consent(Base):
    __tablename__ = "consents"
    __table_args__ = (UniqueConstraint("user_id", "consent_type", "document_version"),)

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    consent_type = Column(String(40), nullable=False)
    document_version = Column(String(32), nullable=False)
    accepted_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(String(512), nullable=True)


class ReceiptDraft(Base):
    """Токен подтверждения с владельцем. Фото и содержимое черновика живут в браузере."""

    __tablename__ = "receipt_drafts"
    id = Column(Uuid, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, server_default=func.now(), nullable=False)


class Receipt(Base):
    """Кассовый чек."""

    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    draft_id = Column(Uuid, ForeignKey("receipt_drafts.id"), unique=True, index=True)
    store_name = Column(String(256), nullable=True)
    date = Column(Date, nullable=True)
    total = Column(Float, default=0.0, nullable=False)
    discount = Column(Float, nullable=True)
    price_comparable = Column(Boolean, nullable=True)
    raw_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Связи
    user = relationship("User", back_populates="receipts")
    items = relationship(
        "Item", back_populates="receipt",
        lazy="selectin", cascade="all, delete-orphan"
    )

    @property
    def accounting_date(self):
        return self.date if self.draft_id is not None and self.date is not None else reporting_day(self.created_at)

    def __repr__(self) -> str:
        return f"<Receipt id={self.id} store={self.store_name} total={self.total}>"


class Item(Base):
    """Позиция в чеке."""

    __tablename__ = "items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id"), nullable=False, index=True)
    name = Column(String(256), nullable=False)
    raw_name = Column(String(256), nullable=True)
    brand = Column(String(128), nullable=True)
    quantity = Column(Float, nullable=True)
    unit = Column(String(2), nullable=True)
    price = Column(Float, nullable=True)
    discount = Column(Float, nullable=True)
    total = Column(Float, default=0.0, nullable=False)
    category = Column(String(64), default="Другое", nullable=False)
    package_size = Column(Float, nullable=True)
    package_unit = Column(String(2), nullable=True)

    # Связь с чеком
    receipt = relationship("Receipt", back_populates="items")

    def __repr__(self) -> str:
        return f"<Item name={self.name} category={self.category} total={self.total}>"
