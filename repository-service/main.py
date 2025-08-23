from fastapi import FastAPI, HTTPException, status
from datetime import datetime
from vectorstore import VectorStoreManager

app = FastAPI(title="ComposureCI Repository", version="0.1.0")

vs_manager = VectorStoreManager()

@app.get("/")
async def root():
    return {"message": "ComposureCI Repository Service", "status": "running"}

@app.get("/api/v1/health")
async def health():
    status = vs_manager.get_status()

    return {
        "status": "healthy", 
        "timestamp": datetime.now().isoformat(),
        "service": "repository",
        "vector_store": "ready" if status["initialized"] else "not_initialized",
        "directories": {
            "service_dir": status["service_dir"],
            "service_dir_exists": status["service_dir_exists"],
            "persist_dir": status["persist_dir"],
            "persist_dir_exists": status["persist_dir_exists"],
            "markdown_files_count": status["markdown_files_count"]
        }
    }

@app.post("/api/v1/vector-store/startup", status_code=status.HTTP_200_OK)
async def startup():
    try:
        initialized = vs_manager.initialize_vectorstore()
        
        if initialized:
            print(f"Successfully loaded existing vectorstore from {vs_manager.persist_dir}")
            return {
                "status": "success",
                "message": "Successfully loaded existing vectorstore from {vs_manager.persist_dir}",
            }
        else:
            print(f"No existing vectorstore found at {vs_manager.persist_dir}")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="No existing vectorstore found"
            )
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to initialize vectorstore: {str(e)}"
        )
            


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)