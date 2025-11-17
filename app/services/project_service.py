# app/services/project_service.py (REFINED)

import uuid
import shutil
from pathlib import Path
from typing import List, Optional
from fastapi import UploadFile, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from fastapi.concurrency import run_in_threadpool
import json # For safely handling JSON data from Pydantic
from app.db.user_repository import UserRepository # New: User Repository for user data access

import logging
# The logger setup in app/utils/logger.py propagates to all files
logger = logging.getLogger(__name__)

# Conceptual imports (replace with actual classes)
from app.db.project_repository import ProjectRepository # New: Repository for DB interaction
from app.jobs.agent_queue import AgentQueueService # New: Service to push tasks to a worker queue

# Existing models and state (Pydantic)
from app.db.models import Project, ProjectFile, Message, Task, AuditLogEntry
from app.agents.base import VirtualLabState, ConversationMessage, TaskItem, AuditEntry

# --- Service Helper: Storage (Conceptual/Local) ---

class FileStorageService:
    """Abstracts file storage logic (should be S3/GCS in production)."""
    def __init__(self, base_path: str = "storage/projects"):
        self.base_path = Path(base_path)

    async def save_file(self, project_id: str, upload_file: UploadFile) -> ProjectFile:
        """Saves uploaded file and returns a ProjectFile record."""
        file_id = str(uuid.uuid4())
        project_dir = self.base_path / project_id
        project_dir.mkdir(parents=True, exist_ok=True)
        
        file_extension = Path(upload_file.filename).suffix
        safe_filename = f"{file_id}{file_extension}"
        storage_path = str(project_dir / safe_filename)
        
        # WARNING: upload_file.read() is BLOCKING. Replace with async object storage client
        content = await upload_file.read() 
        
        with open(storage_path, "wb") as f:
            f.write(content)
            
        return ProjectFile(
            file_id=file_id,
            project_id=project_id,
            filename=upload_file.filename,
            file_size=len(content),
            storage_path=storage_path, # In Prod, this would be S3/GCS URL
            file_type=upload_file.content_type or "application/octet-stream",
            uploaded_at=datetime.now(timezone.utc)
        )

    def cleanup_project_files(self, project_id: str):
        """Remove project directory on failure."""
        project_dir = self.base_path / project_id
        if project_dir.exists():
            shutil.rmtree(project_dir)

# --- Service Layer: Core Business Logic ---

class ProjectService:
    """Service layer for project operations."""
    
    def __init__(self, 
                 repository: ProjectRepository, 
                 user_repository: UserRepository,
                 storage_service: FileStorageService,
                 agent_queue: AgentQueueService):
        # Dependencies injected (IoC)
        self._repo = repository
        self._user_repo = user_repository
        self._storage = storage_service
        self._agent_queue = agent_queue
    
    async def start_new_project(
        self,
        owner_id: str,
        original_research_goal: str,
        context_docs: Optional[List[UploadFile]] = None
    ) -> Project:
        """
        Initiates a new project: saves files, creates DB record, and queues agent task.
        
        Returns:
            The initial Project model (202 Accepted response data).
        """
        logger.info(
            "Starting new project transaction", 
            extra={"owner_id": owner_id, "goal": original_research_goal}
        )
        

        # 1. Create initial Project Model & State
        project_id = str(uuid.uuid4())
        
        # The first message from the user
        initial_message = ConversationMessage(role="user", content=original_research_goal)

        # Initial Audit Log entry
        initial_audit = AuditEntry(
            # 1. immutable schema obj in schema so we stated that in pydantic
            # 2. we want datetime obj internally 
            timestamp=datetime.now(timezone.utc).isoformat(),  #.iso() ONLY USE FOR pydnatic INPUT
            agent="user",
            action="Project Initiated",
            current_phase="intake",
            details={"goal": original_research_goal}
        )
        
        # Initial Virtual Lab State
        initial_state = VirtualLabState(
            messages=[initial_message],
            task_list=[],
            scratchpad={},
            next_agent="pi_agent",
            audit_log=[initial_audit],
            current_phase="intake"
        )
        
        # Create Project DB record (without committing yet)
        project = Project(
            project_id=project_id,
            owner_id=owner_id,
            original_research_goal=original_research_goal,
            current_phase=initial_state.current_phase,
            next_agent=initial_state.next_agent,
        )
        
        # 2. Store Files and Create File Records (Transactional)
        file_records: List[ProjectFile] = []
        try:
            if context_docs:
                for upload_file in context_docs:
                    # Note: We rely on the storage service to handle the I/O
                    file_record = await self._storage.save_file(project_id, upload_file)
                    file_records.append(file_record)
            
            # 3. Persist Project and File Metadata
            # We must use a single commit here for atomicity (Project + Files)
            await run_in_threadpool(self._repo.create_project_and_files, project, file_records)

            # We must use run_in_threadpool because the UserRepository call is synchronous (blocking I/O).
            user = await run_in_threadpool(self._user_repo.get_user_by_id, owner_id)
            
            if not user:
                 # CRITICAL: Crash if user doesn't exist, as Auth passed but DB failed.
                 raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found after authentication.")
            
            # Construct the metadata package for the AI
            user_metadata = {
                "user_id": user.user_id, # Always good to pass the ID for context
                "profession": user.profession,
                "institution": user.institute,
            }
            
            # 4. Asynchronously Trigger Agent (DECOUPLED)
            # Send the core data to the queue. The worker will process it.
            await self._agent_queue.enqueue_agent_task(
                project_id=project_id,
                agent_name="pi_agent",
                task_data={
                    "original_research_goal": original_research_goal,
                    "context_file_paths": [f.storage_path for f in file_records],
                    "user_metadata": user_metadata,
                }
            )
            logger.info(
                "Project created and task queued successfully", 
                extra={"project_id": project.project_id, "user_role": user.profession}
            )

            # 5. Return the newly created Project record immediately (202 Accepted)
            return project
            
        except Exception as e:
            # On ANY failure (DB or File Save), rollback DB and clean storage
            self._storage.cleanup_project_files(project_id)
            raise e
            
    # NOTE: The _save_state_to_db logic is now moved to the ASYNC WORKER
    # The worker will fetch the project, run the agent, and then call a repository 
    # method to update all related tables (Messages, Tasks, AuditLog).