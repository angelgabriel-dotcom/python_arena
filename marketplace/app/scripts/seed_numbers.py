#!/usr/bin/env python3
"""
Seed script to populate the database with sample US phone numbers.
Run this after setting up the database: python -m app.scripts.seed_numbers
"""
import asyncio
from decimal import Decimal
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker, init_db
from app.models.phone_number import PhoneNumber


SAMPLE_NUMBERS = [
    # New York area codes
    {"number": "+12125550164", "price": Decimal("5.00"), "area_code": "212"},
    {"number": "+12125550173", "price": Decimal("5.00"), "area_code": "212"},
    {"number": "+12125550189", "price": Decimal("5.00"), "area_code": "212"},
    {"number": "+12125550192", "price": Decimal("5.00"), "area_code": "212"},
    {"number": "+12125550134", "price": Decimal("5.00"), "area_code": "212"},
    # Los Angeles area codes
    {"number": "+13105550170", "price": Decimal("5.00"), "area_code": "310"},
    {"number": "+13105550185", "price": Decimal("5.00"), "area_code": "310"},
    {"number": "+13105550192", "price": Decimal("5.00"), "area_code": "310"},
    {"number": "+13105550147", "price": Decimal("5.00"), "area_code": "310"},
    {"number": "+13105550123", "price": Decimal("5.00"), "area_code": "310"},
    # Chicago area codes
    {"number": "+13125550139", "price": Decimal("5.00"), "area_code": "312"},
    {"number": "+13125550145", "price": Decimal("5.00"), "area_code": "312"},
    {"number": "+13125550156", "price": Decimal("5.00"), "area_code": "312"},
    {"number": "+13125550167", "price": Decimal("5.00"), "area_code": "312"},
    {"number": "+13125550178", "price": Decimal("5.00"), "area_code": "312"},
    # San Francisco area codes
    {"number": "+14155550145", "price": Decimal("5.00"), "area_code": "415"},
    {"number": "+14155550156", "price": Decimal("5.00"), "area_code": "415"},
    {"number": "+14155550167", "price": Decimal("5.00"), "area_code": "415"},
    {"number": "+14155550178", "price": Decimal("5.00"), "area_code": "415"},
    {"number": "+14155550189", "price": Decimal("5.00"), "area_code": "415"},
    # Miami area codes
    {"number": "+13055550152", "price": Decimal("5.00"), "area_code": "305"},
    {"number": "+13055550163", "price": Decimal("5.00"), "area_code": "305"},
    {"number": "+13055550174", "price": Decimal("5.00"), "area_code": "305"},
    {"number": "+13055550185", "price": Decimal("5.00"), "area_code": "305"},
    {"number": "+13055550196", "price": Decimal("5.00"), "area_code": "305"},
    # Other major US area codes
    {"number": "+12025550100", "price": Decimal("5.00"), "area_code": "202"},  # Washington DC
    {"number": "+12025550111", "price": Decimal("5.00"), "area_code": "202"},
    {"number": "+16175550100", "price": Decimal("5.00"), "area_code": "617"},  # Boston
    {"number": "+16175550111", "price": Decimal("5.00"), "area_code": "617"},
    {"number": "+12135550100", "price": Decimal("5.00"), "area_code": "213"},  # LA downtown
    {"number": "+12135550111", "price": Decimal("5.00"), "area_code": "213"},
    {"number": "+17135550100", "price": Decimal("5.00"), "area_code": "713"},  # Houston
    {"number": "+17135550111", "price": Decimal("5.00"), "area_code": "713"},
    {"number": "+14045550100", "price": Decimal("5.00"), "area_code": "404"},  # Atlanta
    {"number": "+14045550111", "price": Decimal("5.00"), "area_code": "404"},
]


async def seed_numbers(db: AsyncSession) -> int:
    """Seed the database with sample phone numbers."""
    count = 0
    for num_data in SAMPLE_NUMBERS:
        # Check if already exists
        from sqlalchemy import select
        result = await db.execute(
            select(PhoneNumber).where(PhoneNumber.number == num_data["number"])
        )
        if result.scalar_one_or_none():
            print(f"Skipping {num_data['number']} - already exists")
            continue

        phone = PhoneNumber(
            id=uuid.uuid4(),
            number=num_data["number"],
            price=num_data["price"],
            area_code=num_data["area_code"],
            is_available=True,
        )
        db.add(phone)
        count += 1
        print(f"Added {num_data['number']} (${num_data['price']})")

    await db.commit()
    return count


async def main():
    await init_db()

    async with async_session_maker() as db:
        count = await seed_numbers(db)
        print(f"\nSeeded {count} phone numbers")


if __name__ == "__main__":
    asyncio.run(main())