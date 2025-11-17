# tests/conftest.py

import pytest
from fastapi.testclient import TestClient
from app.main import app # Assuming app/main.py defines the app instance
from unittest.mock import MagicMock

# --- Shared Fixtures ---

# 1. FastAPI Test Client Fixture
@pytest.fixture(scope="module")
def client():
    """Provides a TestClient instance for the FastAPI app."""
    return TestClient(app)

# 2. Mock Service Fixture (Used to isolate the API tests)
@pytest.fixture
def mock_project_service(mocker):
    """
    Provides a mock version of the ProjectService for overriding 
    the live dependency in the API tests.
    """
    # Create a mock instance of the service
    mock_service = MagicMock()
    
    # We stub out the method called by the router
    # project_id and other fields are needed to satisfy the response Pydantic model
    mock_project = MagicMock(
        project_id="test-1234", 
        research_goal="Test Goal", 
        next_agent="user_approval"
    )
    mock_service.start_new_project = mocker.AsyncMock(return_value=mock_project)
    
    return mock_service

# 3. Dependency Overrides Fixture (The actual injection)
@pytest.fixture(autouse=True)
def override_dependencies(mock_project_service):
    """
    Temporarily overrides the live ProjectService dependency 
    with the mock version for every API test.
    """
    from app.dependencies import get_project_service
    
    # CRITICAL STEP: Use FastAPI's dependency override feature
    app.dependency_overrides[get_project_service] = lambda: mock_project_service
    
    # Yield control back to the test (where the test runs)
    yield
    
    # CLEANUP: Remove the override after the test finishes
    app.dependency_overrides.clear()