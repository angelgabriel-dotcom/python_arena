import uuid
from datetime import datetime
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class PhoneNumber(Base):
    __tablename__ = "phone_numbers"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    number: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    price: Mapped[Decimal] = mapped_column(nullable=False)  # Price in USD
    is_available: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    area_code: Mapped[str | None] = mapped_column(String(10), nullable=True, index=True)
    twilio_sid: Mapped[str | None] = mapped_column(String(50), nullable=True)  # Twilio SID
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )
    purchased_by_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    purchased_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    # Relationships
    purchased_by: Mapped["User"] = relationship(back_populates="purchased_numbers")

    __table_args__ = (
        Index("ix_phone_numbers_available_area", "is_available", "area_code"),
    )

    def __repr__(self) -> str:
        return f"<PhoneNumber(number={self.number}, price={self.price}, available={self.is_available})>"