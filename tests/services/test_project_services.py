# tests/services/test_project_service.py

import pytest
from unittest.mock import MagicMock
from app.services.project_service import ProjectService 

@pytest.mark.asyncio
async def test_start_new_project_orchestration(mocker):
    # ARRANGE: Mock all external dependencies
    mock_repo = MagicMock()
    mock_storage = MagicMock()
    mock_queue = MagicMock()

    # Stub the return value of file storage to return a mock file record
    mock_file_record = MagicMock(storage_path="/local/path/file.txt")
    mock_storage.save_file = mocker.AsyncMock(return_value=mock_file_record)
    
    # ARRANGE: Instantiate the service with the mocked dependencies
    service = ProjectService(mock_repo, mock_storage, mock_queue)
    
    # ACT: Call the service method
    await service.start_new_project(
        owner_id="u1",
        research_goal="Test Goal",
        context_docs=[MagicMock()] # Pass a mock UploadFile
    )
    
    # ASSERTIONS: Ensure Orchestration was correct
    
    # 1. File was saved
    mock_storage.save_file.assert_called_once()
    
    # 2. Data was persisted atomically
    mock_repo.create_project_and_files.assert_called_once()
    
    # 3. Agent task was queued asynchronously
    mock_queue.enqueue_agent_task.assert_called_once()
    
    # 4. Ensure cleanup was NOT called on success
    mock_storage.cleanup_project_files.assert_not_called()