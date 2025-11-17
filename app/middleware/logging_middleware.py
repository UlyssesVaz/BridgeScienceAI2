# app/middleware/logging_middleware.py

#we inject a unique request ID into logs for tracing
import uuid
import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)

class RequestIDMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        # 1. Generate or retrieve Request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        
        # 2. CRITICAL: Inject the ID into the logger's context (simulated here)
        # In a real setup, we use libraries like loguru or special context variables
        
        # For this minimal setup, we'll log the start/end and pass it in the response header
        
        logger.info("Request started", extra={"request_id": request_id, "path": request.url.path, "method": request.method})
        
        response = await call_next(request)
        
        # 3. Add the ID to the response header
        response.headers["X-Request-ID"] = request_id
        
        logger.info("Request finished", extra={"request_id": request_id, "status_code": response.status_code})
        
        return response