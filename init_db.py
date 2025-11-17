"""Initialize database tables."""

from app.database import engine, Base
from app.db.models import User, Project, ProjectFile, Message, Task, AuditLogEntry

def init_db():
    """Create all database tables."""
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")

if __name__ == "__main__":
    init_db()
