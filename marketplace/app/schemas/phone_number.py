from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional
from uuid import UUID
from pydantic import BaseModel, Field


class PhoneNumberResponse(BaseModel):
    id: UUID
    number: str
    price: Decimal
    is_available: bool
    area_code: str | None
    twilio_sid: str | None
    purchased_by_id: UUID | None
    purchased_at: datetime | None
    created_at: datetime

    class Config:
        from_attributes = True


class PhoneNumberList(BaseModel):
    phone_numbers: list[PhoneNumberResponse]
    total: int
    page: int
    per_page: int
    total_pages: int


class PhoneNumberCreate(BaseModel):
    number: str = Field(min_length=10, max_length=20)
    price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    area_code: str | None = Field(default=None, max_length=10)


class PhoneNumberUpdate(BaseModel):
    price: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    is_available: bool | None = None


class PurchaseRequest(BaseModel):
    phone_number_id: str


class PurchaseResponse(BaseModel):
    message: str
    phone_number: PhoneNumberResponse
    new_balance: Decimal