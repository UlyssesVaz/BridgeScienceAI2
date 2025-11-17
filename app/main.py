# app/main.py
from fastapi import FastAPI
from app.api.v1 import api_router
from app.middleware.logging_middleware import RequestIDMiddleware

app = FastAPI(title="Research Assistant API", version="1.0.0")

# Include API routes
app.include_router(api_router)
app.add_middleware(RequestIDMiddleware) 
app.include_router(api_router)

@app.get("/health")
async def health_check():
    return {"status": "healthy"}