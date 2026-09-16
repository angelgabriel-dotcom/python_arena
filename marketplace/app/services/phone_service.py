from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.phone_number import PhoneNumber
from app.models.user import User
from app.schemas.phone_number import PhoneNumberCreate
from app.services.wallet_service import WalletService
from app.utils.twilio_client import TwilioClient


class PhoneService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.twilio = TwilioClient()
        self.wallet_service = WalletService(db)

    async def search_available_numbers(
        self,
        area_code: Optional[str] = None,
        contains: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[PhoneNumber]:
        """Search available phone numbers in our inventory."""
        query = select(PhoneNumber).where(PhoneNumber.is_available == True)

        if area_code:
            query = query.where(PhoneNumber.area_code == area_code)
        if contains:
            query = query.where(PhoneNumber.number.contains(contains))

        query = query.offset(offset).limit(limit)
        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_number_by_id(self, number_id: UUID) -> Optional[PhoneNumber]:
        """Get a phone number by ID."""
        result = await self.db.execute(
            select(PhoneNumber).where(PhoneNumber.id == number_id)
        )
        return result.scalar_one_or_none()

    async def get_number_by_number(self, number: str) -> Optional[PhoneNumber]:
        """Get a phone number by its number string."""
        result = await self.db.execute(
            select(PhoneNumber).where(PhoneNumber.number == number)
        )
        return result.scalar_one_or_none()

    async def provision_from_twilio(
        self,
        area_code: Optional[str] = None,
        contains: Optional[str] = None,
        limit: int = 10,
    ) -> list[PhoneNumberCreate]:
        """Search and provision new numbers from Twilio."""
        twilio_numbers = await self.twilio.search_phone_numbers(
            area_code=area_code,
            contains=contains,
            limit=limit,
        )

        created_numbers = []
        for tn in twilio_numbers:
            # Check if already in our inventory
            existing = await self.get_number_by_number(tn["number"])
            if existing:
                continue

            phone_create = PhoneNumberCreate(
                number=tn["number"],
                price=Decimal(str(tn["price"])),  # Twilio price in USD, convert as needed
                area_code=tn.get("area_code"),
            )
            created_numbers.append(phone_create)

        return created_numbers

    async def add_to_inventory(self, phone_data: PhoneNumberCreate) -> PhoneNumber:
        """Add a phone number to our inventory."""
        phone = PhoneNumber(
            number=phone_data.number,
            price=phone_data.price,
            area_code=phone_data.area_code,
            is_available=True,
        )
        self.db.add(phone)
        await self.db.commit()
        await self.db.refresh(phone)
        return phone

    async def purchase_number(
        self,
        user: User,
        phone_number_id: UUID,
    ) -> PhoneNumber:
        """Purchase a phone number for a user."""
        phone = await self.get_number_by_id(phone_number_id)
        if not phone:
            raise ValueError("Phone number not found")
        if not phone.is_available:
            raise ValueError("Phone number is not available")

        # Check wallet balance and deduct funds
        # Convert USD price to NGN (approximate rate, in production use real exchange rate)
        USD_TO_NGN_RATE = Decimal("1500")  # Approximate rate
        price_ngn = phone.price * USD_TO_NGN_RATE

        # Create a pending transaction first
        from app.models.user import Transaction, TransactionStatus, TransactionType
        transaction = Transaction(
            wallet_id=(await self.wallet_service.get_or_create_wallet(user.id)).id,
            amount=price_ngn,
            type=TransactionType.PURCHASE,
            status=TransactionStatus.PENDING,
            reference=f"purchase_{phone_number_id}",
            description=f"Purchase of phone number {phone.number}",
        )
        self.db.add(transaction)

        try:
            # Provision the number on Twilio for the user
            twilio_result = await self.twilio.purchase_phone_number(phone.number)

            # Mark transaction as completed
            transaction.status = TransactionStatus.COMPLETED

            # Deduct from wallet
            await self.wallet_service.deduct_funds(
                user_id=user.id,
                amount=price_ngn,
                reference=f"purchase_{phone_number_id}",
                description=f"Purchase of phone number {phone.number}",
            )

            # Mark phone as purchased
            phone.is_available = False
            phone.purchased_by_id = user.id
            phone.purchased_at = phone.updated_at
            phone.twilio_sid = twilio_result.get("sid")  # Store Twilio SID

            await self.db.commit()
            await self.db.refresh(phone)
            return phone
        except Exception as e:
            # Mark transaction as failed
            transaction.status = TransactionStatus.FAILED
            await self.db.commit()
            raise

    async def release_number(self, phone_number_id: UUID) -> PhoneNumber:
        """Release a phone number back to inventory (admin only)."""
        phone = await self.get_number_by_id(phone_number_id)
        if not phone:
            raise ValueError("Phone number not found")

        # Release on Twilio
        await self.twilio.release_phone_number(phone.number)

        phone.is_available = True
        phone.purchased_by_id = None
        phone.purchased_at = None
        phone.twilio_sid = None

        await self.db.commit()
        await self.db.refresh(phone)
        return phone