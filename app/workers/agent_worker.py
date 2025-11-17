# app/workers/agent_worker.py

from typing import Dict, Any
import os
import asyncio
import logging

from redis import Redis
from rq import Worker, Queue

from app.database import SessionLocal
from app.db.project_repository import ProjectRepository  # Repository handles all DB logic
from app.agents.base import VirtualLabState  # Only domain model import needed
from app.agents.pi_agent import PIAgent
from app.agents.analyst_agent import AnalystAgent

logger = logging.getLogger(__name__)


def process_job(project_id: str, agent_name: str, task_data: Dict[str, Any]):
    """
    The function that RQ will call to execute a single task.
    This must be a synchronous function (RQ requirement).
    
    Responsibilities:
    - Orchestrates the job execution flow
    - Delegates DB access to Repository
    - Delegates business logic to Agent
    
    Args:
        project_id: The project ID to process
        agent_name: The name of the agent to execute
        task_data: Dictionary containing:
            - original_research_goal: str
            - context_file_paths: List[str]
            - user_metadata: Dict[str, Any] with user_id, profession, institution
    """
    logger.info(
        f"Starting job processing",
        extra={"project_id": project_id, "agent_name": agent_name}
    )
    
    db = None
    try:
        db = SessionLocal()
        
        # 1. Initialize Repository (encapsulates ALL DB logic)
        repository = ProjectRepository(db_session=db)
        
        # 2. Get project state (Repository handles ORM → Pydantic conversion)
        state = repository.get_project_state(project_id)
        logger.debug(
            f"VirtualLabState loaded from database",
            extra={
                "project_id": project_id,
                "num_messages": len(state.messages),
                "num_tasks": len(state.task_list),
                "num_audit_entries": len(state.audit_log),
                "current_phase": state.current_phase
            }
        )
        
        # 3. Extract task data
        original_research_goal = task_data.get("original_research_goal")
        if not original_research_goal:
            raise ValueError("original_research_goal missing from task_data")
        
        user_metadata = task_data.get("user_metadata", {})
        context_files = task_data.get("context_file_paths", [])
        
        # 4. Execute agent (pure business logic - no DB knowledge)
        if agent_name == "pi_agent":
            agent = PIAgent()
        elif agent_name == "analyst_agent":
            agent = AnalystAgent()
        else:
            logger.warning(f"Unknown agent: {agent_name}. Skipping.")
            raise ValueError(f"Unknown agent: {agent_name}")

        # Execute the agent
        logger.info(f"Executing {agent_name} for project {project_id}")
        final_state = asyncio.run(
            agent.execute(
                state=state,
                original_research_goal=original_research_goal,
                user_metadata=user_metadata,
                context_files=context_files
            )
        )

        logger.info(
            f"Agent execution completed",
            extra={
                "project_id": project_id,
                "agent_name": agent_name,
                "num_tasks_created": len(final_state.task_list),
                "num_messages": len(final_state.messages),
                "next_agent": final_state.next_agent,
                "refined_goal": final_state.scratchpad.get("refined_research_goal", "N/A")[:100]
            }
        )

        # 5. Save results to database
        repository.save_agent_results(project_id, final_state)

        logger.info(
            f"Job completed successfully and results saved to database",
            extra={
                "project_id": project_id,
                "refined_goal": final_state.scratchpad.get("refined_research_goal", "N/A")[:100]
            }
        )

        # 6. AUTO-CHAIN: If next_agent is set and it's not user_approval, queue the next agent
        if final_state.next_agent and final_state.next_agent != "user_approval":
            logger.info(
                f"Auto-chaining to next agent: {final_state.next_agent}",
                extra={"project_id": project_id, "next_agent": final_state.next_agent}
            )

            # Re-queue the next agent job (using asyncio.run since process_job is sync)
            from app.jobs.agent_queue import AgentQueueService
            queue_service = AgentQueueService(queue_name="agent_tasks")

            asyncio.run(
                queue_service.enqueue_agent_task(
                    project_id=project_id,
                    agent_name=final_state.next_agent,
                    task_data=task_data  # Pass same task data forward
                )
            )

            logger.info(f"Next agent {final_state.next_agent} queued successfully")
            
    except Exception as e:
        logger.error(
            f"Error processing job",
            extra={"project_id": project_id, "agent_name": agent_name, "error": str(e)},
            exc_info=True
        )
        raise
    finally:
        # Always close the database session if it was created
        if db is not None:
            db.close()


if __name__ == '__main__':
    """
    Main entry point for the RQ worker.
    This worker continuously polls the Redis queue for jobs.
    """
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    logger.info(f"Starting RQ worker for queue: agent_tasks")
    logger.info(f"Connecting to Redis at: {redis_url}")
    
    try:
        redis_conn = Redis.from_url(redis_url)
        # Test connection
        redis_conn.ping()
        logger.info("Redis connection successful")
        
        queue = Queue("agent_tasks", connection=redis_conn)
        worker = Worker([queue], connection=redis_conn)
        logger.info("Worker initialized. Listening for tasks...")
        worker.work()
    except Exception as e:
        logger.error(f"Failed to start worker: {e}", exc_info=True)
        raise