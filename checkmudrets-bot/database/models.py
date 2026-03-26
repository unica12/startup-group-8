"""Модели базы данных SQLAlchemy для ЧекМудреца."""
from __future__ import annotations

from sqlalchemy import (
    BigInteger, Column, Date, DateTime, Float, ForeignKey,
    Integer, String, Text, func,
)
from sqlalchemy.orm import DeclarativeBase, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    """Пользователь Telegram."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(64), nullable=True)
    first_name = Column(String(128), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    receipts_count = Column(Integer, default=0, nullable=False)

    # Связь с чеками
    receipts = relationship("Receipt", back_populates="user", lazy="selectin")

    def __repr__(self) -> str:
        return f"<User telegram_id={self.telegram_id} username={self.username}>"


class Receipt(Base):
    """Кассовый чек."""

    __tablename__ = "receipts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    store_name = Column(String(256), nullable=True)
    date = Column(Date, nullable=True)
    total = Column(Float, default=0.0, nullable=False)
    raw_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Связи
    user = relationship("User", back_populates="receipts")
    items = relationship(
        "Item", back_populates="receipt",
        lazy="selectin", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Receipt id={self.id} store={self.store_name} total={self.total}>"


class Item(Base):
    """Позиция в чеке."""

    __tablename__ = "items"

    id = Column(Integer, primary_key=True, autoincrement=True)
    receipt_id = Column(Integer, ForeignKey("receipts.id"), nullable=False, index=True)
    name = Column(String(256), nullable=False)
    quantity = Column(Float, default=1.0, nullable=False)
    price = Column(Float, default=0.0, nullable=False)
    total = Column(Float, default=0.0, nullable=False)
    category = Column(String(64), default="Другое", nullable=False)

    # Связь с чеком
    receipt = relationship("Receipt", back_populates="items")

    def __repr__(self) -> str:
        return f"<Item name={self.name} category={self.category} total={self.total}>"
