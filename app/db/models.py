# app/db/models.py (REFINED)

from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, BigInteger, UniqueConstraint
from sqlalchemy.orm import relationship
# from sqlalchemy.dialects.postgresql import JSON # Use for PostgreSQL/JSONB if possible
from sqlalchemy.types import JSON
from app.database import Base 
from datetime import datetime, timezone
import uuid

# Helper for UUID generation
def generate_uuid():
    return str(uuid.uuid4())

# -----------------------------------------------
# User Table
class User(Base):
    __tablename__ = "users"
    # Use generate_uuid for the default PK
    user_id = Column(String(36), primary_key=True, default=generate_uuid) 
    email = Column(String(255), unique=True, index=True) # Added max length for string
    hashed_password = Column(String(100)) # Added max length
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    institute = Column(String(100))
    profession = Column(String(100)) 
    
    projects = relationship("Project", back_populates="owner", cascade="all, delete-orphan")


# Master Project Table
class Project(Base):
    __tablename__ = "projects"
    project_id = Column(String(36), primary_key=True, default=generate_uuid)
    owner_id = Column(String(36), ForeignKey("users.user_id"), index=True)
    
    # Optional: A short, user-editable title for quick identification
    title = Column(String(255), nullable=True) 
    original_research_goal = Column(String) 

    refined_research_goal = Column(String, nullable=True)
    current_phase = Column(String(50), default="intake") # Constrained string length
    next_agent = Column(String(50), nullable=True) # Constrained string length
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="projects")
    
    # CRITICAL: Added cascade for deletion of related records
    files = relationship("ProjectFile", back_populates="project", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="project", cascade="all, delete-orphan")
    audit_entries = relationship("AuditLogEntry", back_populates="project", cascade="all, delete-orphan")
    messages = relationship("Message", back_populates="project", cascade="all, delete-orphan")


# Project File Metadata
class ProjectFile(Base):
    __tablename__ = "project_files"
    file_id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.project_id"), index=True, nullable=False)

    filename = Column(String(255), nullable=False)
    file_size = Column(BigInteger) # REFINED: Safely handles large files
    storage_path = Column(String(500), nullable=False) # Increased length for S3/GCS paths
    file_type = Column(String(50), nullable=False)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="files")


# Stores permanent conversation messages
class Message(Base):
    __tablename__ = "messages"
    message_id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.project_id"), index=True)
    role = Column(String(20), nullable=False) 
    content = Column(String, nullable=False) # Use TEXT for potentially long content
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    project = relationship("Project", back_populates="messages")

# Stores permanent task list items
class Task(Base):
    __tablename__ = "tasks"
    # 1. DB Primary Key (Leave as UUID, let DB manage it)
    db_id = Column(String(36), primary_key=True, default=generate_uuid) 
    # 2. Project Foreign Key
    project_id = Column(String(36), ForeignKey("projects.project_id"), index=True)
    # 3. Agent's Internal ID (This is 't1', 't2', etc.)
    agent_task_id = Column(String(50), nullable=False) # Changed from task_id
    
    # 4. Enforce uniqueness on the *combination* of project and agent ID
    __table_args__ = (
        # Ensures that for any given project_id, the agent_task_id must be unique.
        UniqueConstraint('project_id', 'agent_task_id', name='uq_project_agent_task'),
    )
    description = Column(String, nullable=False)
    status = Column(String(50), default="pending") 
    result = Column(String, nullable=True) # Use TEXT if results can be long
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    project = relationship("Project", back_populates="tasks")

# Stores permanent audit log entries
class AuditLogEntry(Base):
    __tablename__ = "audit_log_entries"
    entry_id = Column(String(36), primary_key=True, default=generate_uuid)
    project_id = Column(String(36), ForeignKey("projects.project_id"), index=True)
    
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False) # Added default
    agent = Column(String(50), nullable=False)
    action = Column(String(255), nullable=False)
    current_phase = Column(String(50), nullable=False)
    # REFINED: Use JSON/JSONB for dynamic details
    details = Column(JSON, nullable=True) 
    
    project = relationship("Project", back_populates="audit_entries")