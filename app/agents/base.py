# app/agents/base.py (REFINED - Pydantic-Based)

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

# CRITICAL: Import the clean, structured data models (Pydantic)
from app.schemas.project import ConversationMessage, TaskItem, AuditEntry
from pydantic import BaseModel

# We will define the VirtualLabState using Pydantic, but add the helper methods you wrote.

class VirtualLabState(BaseModel):
    """
    The complete, ephemeral state of the virtual lab - the agent's workbench.
    It inherits from Pydantic's BaseModel for validation and safety.
    """
    messages: List[ConversationMessage]
    task_list: List[TaskItem]
    scratchpad: Dict[str, Any]
    next_agent: str
    audit_log: List[AuditEntry]
    current_phase: str = "intake"
    
    # We add the helper methods directly to the Pydantic model instance
    def add_audit_entry(self, agent: str, action: str, details: Dict[str, Any]):
        """Helper to append to the lab notebook."""
        new_entry = AuditEntry(
            timestamp=datetime.now(timezone.utc),
            agent=agent,
            action=action,
            current_phase=self.current_phase,
            details=details
        )
        self.audit_log.append(new_entry)
        
    def to_dict(self) -> Dict[str, Any]:
        """Serialize for API response."""
        # Pydantic's model_dump is the correct way to serialize
        return self.model_dump(mode='json')


class BaseAgent:
    """Base class with interface definition for all agents."""
    
    async def execute(
        self,
        state: VirtualLabState,
        **kwargs
    ) -> VirtualLabState:
        """
        Execute agent logic.
        Takes the workbench, does work, returns updated workbench.
        """
        raise NotImplementedError