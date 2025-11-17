# app/api/v1/endpoints/projects.py (REFINED - SCALABLE)

from typing import List, Optional
from fastapi import APIRouter, Depends, Form, UploadFile, HTTPException, status, Header
from app.services.project_service import ProjectService 

# Import the correct schemas for the ASYNC contract
from app.schemas.project import ProjectCreationResponse

# Import the clean, high-level service dependency
from app.dependencies import get_project_service 

# we are returning a 202 Accepted response for body responses, not anything to do with AUTH.
# auth is still a multipart/form-data endpoint. NEVER CHANGE THAT TO JSON.
from fastapi.responses import JSONResponse


# --- Authentication Dependency (Kept as is - it's great!) ---

async def get_current_user_id(
    authorization: Optional[str] = Header(None)
) -> str:
    """
    TDD-safe auth stub to extract and validate the user ID from the Bearer token.
    """
    scheme, _, token = (authorization or "").partition(" ")
    
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    if token == "TEST_AUTH_TOKEN":
        # Return a deterministic test user ID
        return "test-user-f81d4"

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )


router = APIRouter()

@router.post(
    "/projects", 
    # CRITICAL: Use the 202 ACCEPTED status code
    status_code=status.HTTP_202_ACCEPTED,
    # CRITICAL: Use the ProjectCreationResponse schema for the acknowledgement
    response_model=ProjectCreationResponse, 
)
async def create_project(
    
    # Multipart Form Data (FastAPI handles parsing research_goal and files)
    original_research_goal: str = Form(..., description="The user's primary text prompt."),
    context_docs: Optional[List[UploadFile]] = Form(None, description="One or more context files."),
    
    # Dependencies (Clean, high-level dependencies only)
    owner_id: str = Depends(get_current_user_id),
    project_service: ProjectService = Depends(get_project_service)
):
    """
    Initiates a new research project. This is a non-blocking operation 
    that queues the AI analysis task and immediately returns an acknowledgement.
    """
    
    if not original_research_goal or not original_research_goal.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="research_goal cannot be empty"
        )
    
    try:
        # 1. Delegate work entirely to the Service layer
        project = await project_service.start_new_project(
            owner_id=owner_id,
            original_research_goal=original_research_goal,
            context_docs=context_docs
        )
        
        # 2. Validate the ORM object into the Pydantic instance (V2 syntax)
        # The 'ProjectCreationResponse' class must be configured with ConfigDict(from_attributes=True)
        validated_instance = ProjectCreationResponse.model_validate(project)
        
        # 3. Use the correct V2 method, .model_copy(), for updating fields
        response_data = validated_instance.model_copy(
            update={
                "status": "accepted",
                # IMPORTANT: DO NOT include project_id or research_goal here, 
                # as they were loaded in Step 2.
            }
        )
        
        # 4. Create the raw JSONResponse object to inject the Location header
        response = JSONResponse(
            content=response_data.model_dump(mode='json'), # Use model_dump to get the serializable dict
            status_code=status.HTTP_202_ACCEPTED
        )
        
        # 5. Inject the standard Location header
        response.headers["Location"] = f"/api/v1/projects/{project.project_id}"
        
        # 6. FINAL RETURN (The only one in the try block)
        return response
        
        
    except Exception as e:
        # Any failure in the Service (DB error, file storage failure) results in a 500
        # The service layer is responsible for the cleanup/rollback
        print(f"Error initiating project for user {owner_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to initiate project. Please try again."
        )
    
    