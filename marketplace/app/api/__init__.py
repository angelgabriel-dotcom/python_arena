from app.api.auth import router as auth_router
from app.api.phone_numbers import router as phone_numbers_router

__all__ = ["auth_router", "phone_numbers_router"]