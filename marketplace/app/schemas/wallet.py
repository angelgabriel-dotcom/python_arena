from datetime import datetime
from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, Field


class WalletBalance(BaseModel):
    balance: Decimal
    currency: str = "NGN"


class DepositInit(BaseModel):
    amount: Decimal = Field(gt=0, max_digits=10, decimal_places=2)


class DepositResponse(BaseModel):
    authorization_url: str
    reference: str
    access_code: str


class TransactionResponse(BaseModel):
    id: str
    amount: Decimal
    type: Literal["deposit", "purchase", "refund"]
    status: Literal["pending", "completed", "failed"]
    reference: str
    description: str | None
    created_at: datetime

    class Config:
        from_attributes = True


class TransactionList(BaseModel):
    transactions: list[TransactionResponse]
    total: int
    page: int
    per_page: int
    total_pages: int