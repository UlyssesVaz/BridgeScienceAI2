# app/schemas/user.py

from pydantic import BaseModel, EmailStr
from datetime import datetime


class UserCreationRequest(BaseModel):
    """Request schema for creating a new user."""
    email: EmailStr
    profession: str
    institute: str


class UserCreationResponse(BaseModel):
    """Response schema for user creation."""
    user_id: str
    email: str
    profession: str
    institute: str
    auth_token: str
    created_at: datetime

    model_config = {"from_attributes": True}
