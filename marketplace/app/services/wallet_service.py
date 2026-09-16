from decimal import Decimal
from typing import Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Transaction, TransactionStatus, TransactionType, Wallet


class WalletService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_wallet(self, user_id: UUID) -> Optional[Wallet]:
        """Get a user's wallet."""
        result = await self.db.execute(
            select(Wallet).where(Wallet.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def create_wallet(self, user_id: UUID, currency: str = "NGN") -> Wallet:
        """Create a wallet for a user."""
        wallet = Wallet(user_id=user_id, balance=Decimal("0"), currency=currency)
        self.db.add(wallet)
        await self.db.commit()
        await self.db.refresh(wallet)
        return wallet

    async def get_or_create_wallet(self, user_id: UUID, currency: str = "NGN") -> Wallet:
        """Get existing wallet or create new one."""
        wallet = await self.get_wallet(user_id)
        if not wallet:
            wallet = await self.create_wallet(user_id, currency)
        return wallet

    async def add_funds(
        self,
        user_id: UUID,
        amount: Decimal,
        reference: str,
        description: Optional[str] = None,
    ) -> Transaction:
        """Add funds to wallet (deposit)."""
        wallet = await self.get_or_create_wallet(user_id)

        # Create transaction record
        transaction = Transaction(
            wallet_id=wallet.id,
            amount=amount,
            type=TransactionType.DEPOSIT,
            status=TransactionStatus.COMPLETED,
            reference=reference,
            description=description or f"Deposit of {amount} {wallet.currency}",
        )
        self.db.add(transaction)

        # Update balance
        wallet.balance += amount

        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction

    async def deduct_funds(
        self,
        user_id: UUID,
        amount: Decimal,
        reference: str,
        description: Optional[str] = None,
    ) -> Transaction:
        """Deduct funds from wallet (purchase)."""
        wallet = await self.get_wallet(user_id)
        if not wallet:
            raise ValueError("Wallet not found")

        if wallet.balance < amount:
            raise ValueError("Insufficient balance")

        # Create transaction record
        transaction = Transaction(
            wallet_id=wallet.id,
            amount=amount,
            type=TransactionType.PURCHASE,
            status=TransactionStatus.COMPLETED,
            reference=reference,
            description=description or f"Purchase of {amount} {wallet.currency}",
        )
        self.db.add(transaction)

        # Update balance
        wallet.balance -= amount

        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction

    async def refund_funds(
        self,
        user_id: UUID,
        amount: Decimal,
        reference: str,
        description: Optional[str] = None,
    ) -> Transaction:
        """Refund funds to wallet."""
        wallet = await self.get_wallet(user_id)
        if not wallet:
            raise ValueError("Wallet not found")

        # Create transaction record
        transaction = Transaction(
            wallet_id=wallet.id,
            amount=amount,
            type=TransactionType.REFUND,
            status=TransactionStatus.COMPLETED,
            reference=reference,
            description=description or f"Refund of {amount} {wallet.currency}",
        )
        self.db.add(transaction)

        # Update balance
        wallet.balance += amount

        await self.db.commit()
        await self.db.refresh(transaction)
        return transaction