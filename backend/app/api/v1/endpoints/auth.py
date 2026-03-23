"""Authentication endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/login")
async def login() -> dict:
    """User login endpoint (placeholder)."""
    return {"message": "Login endpoint - to be implemented"}


@router.post("/register")
async def register() -> dict:
    """User registration endpoint (placeholder)."""
    return {"message": "Register endpoint - to be implemented"}


@router.post("/refresh")
async def refresh_token() -> dict:
    """Token refresh endpoint (placeholder)."""
    return {"message": "Refresh endpoint - to be implemented"}


@router.get("/me")
async def get_current_user() -> dict:
    """Get current user endpoint (placeholder)."""
    return {"message": "Get current user endpoint - to be implemented"}
