from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from typing import Any
import uuid
import httpx

REPOSITORY_URL = "http://repository:8001"

app = FastAPI(title="ComposureCI Orchestrator", version="0.1.0")

class ComposeRequest(BaseModel):
    requirements: str
    constraints: dict[str, Any] = {}

class ComposeResponse(BaseModel):
    composition_id: str
    status: str
    services: list[dict[str, Any]]
    created_at: str
    
compositions = {}

@app.get("/")
async def root():
    return {"message": "ComposureCI Orchestrator API", "status": "running"}

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

@app.get("/api/v1/health/full")
async def full_health():
    """Health check that includes repository service"""
    repository_status = "unknown"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{REPOSITORY_URL}/api/v1/health", timeout=5.0)
            if response.status_code == 200:
                repository_status = "healthy"
                repository_data = response.json()
            else:
                repository_status = f"error_{response.status_code}"
                repository_data = {}
    except Exception as e:
        repository_status = f"connection_error: {str(e)}"
        repository_data = {}
    
    return {
        "repository": {
            "status": repository_status,
            "data": repository_data if repository_status == "healthy" else None
        },
        "overall_status": "healthy" if repository_status == "healthy" else "degraded"
    }


@app.post("/api/v1/compose", response_model=ComposeResponse)
async def compose_services(request: ComposeRequest):
    composition_id = str(uuid.uuid4())
    
    mock_services = [
        {"task": "speech-to-text", "model": "whisper-base", "input": "microphone"},
        {"task": "face-detection", "model": "mtcnn", "input": "camera"},
        {"task": "navigation", "model": "nav2", "input": "goal_pose"}
    ]
    
    composition = {
        "composition_id": composition_id,
        "status": "created",
        "services": mock_services,
        "created_at": datetime.now().isoformat(),
        "requirements": request.requirements,
        "constraints": request.constraints
    }

    compositions[composition_id] = composition
    
    return ComposeResponse(**composition)

@app.get("/api/v1/compositions/{composition_id}")
async def get_composition(composition_id: str):
    if composition_id not in compositions:
        return {"error": "Composition not found"}, 404
    return compositions[composition_id]

@app.post("/api/v1/vector-store/startup")
async def initialize_repository():
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{REPOSITORY_URL}/api/v1/vector-store/startup")
            
            if response.status_code == 200:
            # TODO: fix whatever this is
               print("Hurray") 
                
            else:
                return{
                    "status": "error"
                }
    except Exception as e:
        return {
            "status": "connection error",
            "message": f"Failed to connect to repository service: {str(e)}"
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)