##
#  THIS HAS MOCK DATA WE NEED TO REMOVE immediately
##
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Dict, List, Optional

# This is the security scheme. It tells FastAPI to look
# for the "Authorization: Bearer <token>" header.
security = HTTPBearer()


def get_user_test_metadata(user_id: str) -> Optional[Dict[str, Any]]:
    """Returns test metadata for the TDD user ID."""
    if user_id == "test-user-f81d4":
        return {
            "user_id": "test-user-f81d4",
            "profession": "Senior Virologist", # Your mock data
            "institution": "FANG Research Labs", # Your mock data
        }
    return None

async def get_current_user_id(
    authorization: Optional[str] = Header(None) 
) -> str:
    """
    This is a TDD-safe auth stub.
    It demands a token and checks if it's our one "magic" test token.
    If not, it correctly raises a 401.
    """
    
    # Case 1: Authorization Header is MISSING
    if authorization is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, 
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    # Extract the token (must start with 'Bearer ')
    scheme, _, token = authorization.partition(" ")
    
    # Case 2: Authorization Header is MALFORMED (e.g., missing 'Bearer' prefix)
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Case 3: Authorization Header is VALIDLY FORMATTED BUT INVALID TOKEN
    if token == "TEST_AUTH_TOKEN":
        return "test-user-f81d4"

    # If the token is anything else, it's unauthorized.
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )