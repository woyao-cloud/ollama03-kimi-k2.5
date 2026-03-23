"""User endpoints."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/")
async def list_users() -> dict:
    """List users endpoint (placeholder)."""
    return {"message": "List users endpoint - to be implemented"}


@router.post("/")
async def create_user() -> dict:
    """Create user endpoint (placeholder)."""
    return {"message": "Create user endpoint - to be implemented"}


@router.get("/{user_id}")
async def get_user(user_id: str) -> dict:
    """Get user by ID endpoint (placeholder)."""
    return {"message": f"Get user {user_id} endpoint - to be implemented"}


@router.put("/{user_id}")
async def update_user(user_id: str) -> dict:
    """Update user endpoint (placeholder)."""
    return {"message": f"Update user {user_id} endpoint - to be implemented"}


@router.delete("/{user_id}")
async def delete_user(user_id: str) -> dict:
    """Delete user endpoint (placeholder)."""
    return {"message": f"Delete user {user_id} endpoint - to be implemented"}
