# create_db.py
import os
import sys

# Add the project root to the path so the imports below work
sys.path.append(os.path.dirname(os.path.abspath(__file__))) 

# 1. Import Base and engine
from app.database import Base, engine

# 2. IMPORT ALL YOUR MODELS
# This step is CRUCIAL. Importing them registers them with Base.metadata.
from app.db.models import Project, Task, User, Message, AuditLogEntry, ProjectFile

# 3. Drop existing tables (optional, but ensures a clean start)
# Base.metadata.drop_all(bind=engine) 

# 4. Create all tables defined in models.py
print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created successfully.")