# app/schemas/project.py
# These are Pydantic models for API request/response validation
# app/schemas/project.py (REFINED)

from pydantic import BaseModel, Field, ConfigDict
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime

# --- Sub-models (Kept Clean) ---
class TaskItem(BaseModel):
    id: str
    description: str
    status: Literal["pending", "in_progress", "completed", "failed"]
    result: Optional[Any] = None

class ConversationMessage(BaseModel):
    role: str
    content: str

class AuditEntry(BaseModel):
    # CRITICAL FIX: Ensure 'details' is a dictionary, not a generic string/Any
    timestamp: datetime 
    agent: str
    action: str
    current_phase: str
    details: Dict[str, Any] 

# --- NEW: Request Schema (For clarity/future non-multipart endpoints) ---

class ProjectCreationRequest(BaseModel):
    """Defines the input parameters for creating a project."""
    original_research_goal: str = Field(..., description="The user's primary text prompt.")
    # Note: We can't use this for UploadFiles in a multipart form, but it documents the intent.


# --- NEW: Immediate Response Schema (202 Accepted) ---

class ProjectCreationResponse(BaseModel):
    """
    Response for POST /api/v1/projects. 
    Indicates project creation success and task delegation (202 Accepted logic).
    """
    project_id: str = Field(..., description="The unique ID for the new project.")
    original_research_goal: str
    status: Literal["accepted", "processing"] = "accepted"
    next_agent: Literal["pi_agent", "user_approval"]
    message: str = "Project accepted. AI analysis plan generation is in progress."
    
    model_config = ConfigDict(from_attributes=True) # Allow ORM mapping


# --- Main State Schema (For GET /api/v1/projects/{id}) ---

class VirtualLabState(BaseModel):
    """
    API response for the final state retrieval (GET /{id}). 
    This should NOT be the POST response.
    """
    # Project metadata (from DB)
    project_id: str
    original_research_goal: str # user inputted goal
    refined_research_goal: Optional[str] = None #ai refined goal
    
    # VirtualLabState contents (re-assembled from normalized tables)
    messages: List[ConversationMessage]
    task_list: List[TaskItem]
    scratchpad: Dict[str, Any] # Scratchpad remains ephemeral/JSON in the DB
    next_agent: Literal["pi_agent", "router", "worker", "user_approval"]
    audit_log: List[AuditEntry]
    current_phase: str
    
    model_config = ConfigDict(from_attributes=True)

# ... (Removed VirtualLabStateSchema as it's redundant now) ...

# File info for other endpoints
class ProjectFileInfo(BaseModel):
    file_id: str
    filename: str
    file_size: int
    file_type: str
    uploaded_at: datetime
    
    model_config = ConfigDict(from_attributes=True)