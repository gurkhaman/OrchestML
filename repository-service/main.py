from fastapi import FastAPI
from pydantic import BaseModel
from typing import Any
import chromadb
from datetime import datetime

app = FastAPI(title="ComposureCI Repository", version="0.1.0")


MOCK_SERVICES = [
    {
        "id": "whisper-base",
        "name": "Whisper Speech-to-Text",
        "task": "speech-to-text",
        "description": "OpenAI Whisper model for speech recognition",
        "input_type": "audio",
        "output_type": "text",
        "model_hub": "huggingface",
        "model_path": "openai/whisper-base"
    },
    {
        "id": "mtcnn-face",
        "name": "MTCNN Face Detection", 
        "task": "face-detection",
        "description": "Multi-task CNN for face detection and recognition",
        "input_type": "image",
        "output_type": "bounding_boxes",
        "model_hub": "pytorch",
        "model_path": "mtcnn"
    },
    {
        "id": "nav2-navigation",
        "name": "Nav2 Navigation Stack",
        "task": "navigation", 
        "description": "ROS2 navigation stack for autonomous navigation",
        "input_type": "goal_pose",
        "output_type": "cmd_vel",
        "model_hub": "ros",
        "model_path": "nav2"
    }
]

@app.get("/")
async def root():
    return {"message": "ComposureCI Repository Service", "status": "running"}

@app.get("/api/v1/health")
async def health():
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)