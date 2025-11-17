# tests/api/test_projects.py

from fastapi.testclient import TestClient
from app.main import app # Assuming your main app instance is named 'app'
from fastapi import status
from unittest.mock import MagicMock

client = TestClient(app)

def test_create_project_202_success(mocker):
    # 1. MOCK: Mock the service layer's core method.
    # We ensure the test passes *if* the router calls the service correctly.
    mock_project = MagicMock(project_id="test-123", original_research_goal="Test Goal", next_agent="pi_agent")
    
    # Mock the Dependency Injection for the Project Service
    # NOTE: You'll need to update your app/dependencies.py to allow overriding dependencies
    mocker.patch(
        "app.dependencies.get_project_service", 
        return_value=MagicMock(start_new_project=mocker.AsyncMock(return_value=mock_project))
    )

    # 2. ACT: Send the multipart/form-data request using 'files' parameter
    response = client.post(
        "/api/v1/projects",
        headers={"Authorization": "Bearer TEST_AUTH_TOKEN"},
        data={
            "research_goal": "Analyze the new KP.3 variant"
        },
        files={
            "context_docs": ("brief.txt", b"file content", "text/plain")
        }
    )

    # 3. ASSERT: Enforce the Asynchronous Contract
    assert response.status_code == status.HTTP_202_ACCEPTED
    
    # 4. ASSERT: Enforce the Location Header Best Practice
    assert "Location" in response.headers
    assert response.headers["Location"] == "/api/v1/projects/test-123"

    # 5. ASSERT: Enforce the Response Body Contract
    data = response.json()
    assert data["project_id"] == "test-123"
    assert data["status"] == "accepted"
    assert data["next_agent"] == "pi_agent" 
    
    # 6. ASSERT: Ensure the service was actually called
    # (If you mocked the service correctly, you'd assert the mock was called with the right args)