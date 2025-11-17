# app/api/v1/endpoints/users.py

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.schemas.user import UserCreationRequest, UserCreationResponse
from app.db.user_repository import UserRepository
from app.dependencies import get_user_repository

import secrets

router = APIRouter()


@router.post(
    "/users",
    status_code=status.HTTP_201_CREATED,
    response_model=UserCreationResponse
)
async def create_user(
    request: UserCreationRequest,
    repository: UserRepository = Depends(get_user_repository)
):
    """
    Create a new user account.

    This is a simple onboarding endpoint that creates a user with email,
    profession, and institution metadata.

    TODO: Replace with OAuth2 authentication in the future.

    Args:
        request: User creation request with email, profession, institute
        repository: Injected UserRepository dependency

    Returns:
        UserCreationResponse with user_id and auth_token

    Raises:
        409 Conflict: If email already exists
        500 Internal Server Error: If database operation fails
    """
    try:
        # Create user in database (runs in threadpool for async compatibility)
        user = await run_in_threadpool(
            repository.create_user,
            email=request.email,
            profession=request.profession,
            institute=request.institute
        )

        # Generate a simple auth token (TODO: Replace with proper OAuth)
        # For now, using a secure random token
        auth_token = f"usr_{user.user_id}_{secrets.token_urlsafe(16)}"

        # Return user details with auth token
        return UserCreationResponse(
            user_id=user.user_id,
            email=user.email,
            profession=user.profession,
            institute=user.institute,
            auth_token=auth_token,
            created_at=user.created_at
        )

    except ValueError as e:
        # User already exists
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e)
        )
    except Exception as e:
        # Unexpected error
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )
