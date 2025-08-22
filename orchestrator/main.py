from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from typing import Any
import uuid

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)