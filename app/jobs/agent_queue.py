# app/jobs/agent_queue.py

from typing import Dict, Any, Optional
from datetime import datetime, timezone
import os
from redis import Redis
from rq import Queue
import logging
from fastapi.concurrency import run_in_threadpool
from app.workers.agent_worker import process_job

logger = logging.getLogger(__name__)

class AgentQueueService:
    """
    Service to abstract the job queue mechanism using Redis Queue (RQ).
    FastAPI calls this to delegate work.
    """
    def __init__(self, queue_name: str = "agent_tasks"):
        self.queue_name = queue_name
        # Get Redis URL from environment, default to localhost
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        try:
            # Initialize Redis connection
            self.redis_conn = Redis.from_url(redis_url)
            # Test connection
            self.redis_conn.ping()
            # Initialize RQ Queue
            self.queue = Queue(self.queue_name, connection=self.redis_conn)
            logger.info(f"AgentQueueService initialized with queue: {self.queue_name}")
        except Exception as e:
            logger.error(f"Failed to connect to Redis at {redis_url}: {e}")
            raise

    async def enqueue_agent_task(
        self, 
        project_id: str, 
        agent_name: str, 
        task_data: Dict[str, Any]
    ) -> bool:
        """
        Pushes a task payload to the queue. Returns True if successfully queued.
        """
        try:
            # Enqueue the job - RQ will call app.workers.agent_worker.process_job
            # with the arguments: project_id, agent_name, task_data
            #Wrap synchronous RQ enqueue in threadpool (don't block async event loop)
            job = await run_in_threadpool(
                self.queue.enqueue,
                process_job,
                project_id,
                agent_name,
                task_data,
                job_timeout="10m"  # Allow up to 10 minutes for job execution
            )
            logger.info(
                f"Job queued successfully",
                extra={
                    "project_id": project_id,
                    "agent_name": agent_name,
                    "job_id": job.id,
                    "queue": self.queue_name
                }
            )
            return True
        except Exception as e:
            logger.error(
                f"Failed to enqueue job",
                extra={"project_id": project_id, "error": str(e)},
                exc_info=True
            )
            raise