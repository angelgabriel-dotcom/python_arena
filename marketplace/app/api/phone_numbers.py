from decimal import Decimal
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.auth import get_current_user
from app.database import get_db
from app.models.user import User
from app.schemas.phone_number import (
    PhoneNumberCreate,
    PhoneNumberList,
    PhoneNumberResponse,
    PhoneNumberUpdate,
    PurchaseRequest,
    PurchaseResponse,
)
from app.services.phone_service import PhoneService

router = APIRouter(prefix="/phone-numbers", tags=["phone-numbers"])


def get_phone_service(db: AsyncSession = Depends(get_db)) -> PhoneService:
    return PhoneService(db)


@router.get("", response_model=PhoneNumberList)
async def list_phone_numbers(
    area_code: Optional[str] = Query(None, description="Filter by area code (e.g., 212)"),
    contains: Optional[str] = Query(None, description="Filter by number pattern"),
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    phone_service: PhoneService = Depends(get_phone_service),
):
    """List available phone numbers in inventory."""
    offset = (page - 1) * per_page
    numbers = await phone_service.search_available_numbers(
        area_code=area_code,
        contains=contains,
        limit=per_page,
        offset=offset,
    )

    # Get total count
    from sqlalchemy import select, func
    from app.models.phone_number import PhoneNumber
    total_query = select(func.count(PhoneNumber.id)).where(PhoneNumber.is_available == True)
    if area_code:
        total_query = total_query.where(PhoneNumber.area_code == area_code)
    if contains:
        total_query = total_query.where(PhoneNumber.number.contains(contains))
    total_result = await phone_service.db.execute(total_query)
    total = total_result.scalar() or 0

    return PhoneNumberList(
        phone_numbers=[PhoneNumberResponse.model_validate(n) for n in numbers],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=(total + per_page - 1) // per_page,
    )


@router.get("/search-twilio", response_model=list[PhoneNumberCreate])
async def search_twilio_numbers(
    area_code: Optional[str] = Query(None, description="Area code to search (e.g., 212)"),
    contains: Optional[str] = Query(None, description="Pattern to match in number"),
    limit: int = Query(10, ge=1, le=50, description="Max results"),
    phone_service: PhoneService = Depends(get_phone_service),
):
    """Search for available numbers on Twilio (provision new inventory)."""
    try:
        numbers = await phone_service.provision_from_twilio(
            area_code=area_code,
            contains=contains,
            limit=limit,
        )
        return numbers
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )


@router.post("", response_model=PhoneNumberResponse, status_code=status.HTTP_201_CREATED)
async def add_phone_number(
    phone_data: PhoneNumberCreate,
    phone_service: PhoneService = Depends(get_phone_service),
    current_user: User = Depends(get_current_user),
):
    """Add a phone number to inventory (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can add phone numbers to inventory",
        )

    # Check if number already exists
    existing = await phone_service.get_number_by_number(phone_data.number)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Phone number already exists in inventory",
        )

    phone = await phone_service.add_to_inventory(phone_data)
    return PhoneNumberResponse.model_validate(phone)


@router.get("/{number_id}", response_model=PhoneNumberResponse)
async def get_phone_number(
    number_id: UUID,
    phone_service: PhoneService = Depends(get_phone_service),
):
    """Get a phone number by ID."""
    phone = await phone_service.get_number_by_id(number_id)
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not found",
        )
    return PhoneNumberResponse.model_validate(phone)


@router.patch("/{number_id}", response_model=PhoneNumberResponse)
async def update_phone_number(
    number_id: UUID,
    phone_update: PhoneNumberUpdate,
    phone_service: PhoneService = Depends(get_phone_service),
    current_user: User = Depends(get_current_user),
):
    """Update a phone number (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can update phone numbers",
        )

    phone = await phone_service.get_number_by_id(number_id)
    if not phone:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Phone number not found",
        )

    if phone_update.price is not None:
        phone.price = phone_update.price
    if phone_update.is_available is not None:
        phone.is_available = phone_update.is_available

    await phone_service.db.commit()
    await phone_service.db.refresh(phone)
    return PhoneNumberResponse.model_validate(phone)


@router.post("/purchase", response_model=PurchaseResponse)
async def purchase_phone_number(
    purchase_request: PurchaseRequest,
    phone_service: PhoneService = Depends(get_phone_service),
    current_user: User = Depends(get_current_user),
):
    """Purchase a phone number."""
    try:
        phone_number_id = UUID(purchase_request.phone_number_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid phone number ID",
        )

    try:
        phone = await phone_service.purchase_number(current_user, phone_number_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )

    # TODO: Get actual wallet balance after purchase
    from app.services.wallet_service import WalletService
    wallet_service = WalletService(phone_service.db)
    wallet = await wallet_service.get_wallet(current_user.id)
    new_balance = wallet.balance if wallet else Decimal("0")

    return PurchaseResponse(
        message="Phone number purchased successfully",
        phone_number=PhoneNumberResponse.model_validate(phone),
        new_balance=new_balance,
    )


@router.post("/{number_id}/release", response_model=PhoneNumberResponse)
async def release_phone_number(
    number_id: UUID,
    phone_service: PhoneService = Depends(get_phone_service),
    current_user: User = Depends(get_current_user),
):
    """Release a phone number back to inventory (admin only)."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admins can release phone numbers",
        )

    try:
        phone = await phone_service.release_number(number_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e),
        )

    return PhoneNumberResponse.model_validate(phone)