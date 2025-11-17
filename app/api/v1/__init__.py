# app/api/v1/__init__.py (REFINED)

from fastapi import APIRouter
# Assuming the actual endpoint logic is in app/api/v1/endpoints/projects.py
from .endpoints import projects 

# Set the version prefix ONLY once here.
api_router = APIRouter(prefix="/api/v1") 

# The projects router will define its path *relative* to this prefix,
# e.g., if it has /projects, the final path is /api/v1/projects.
api_router.include_router(projects.router, tags=["projects"])