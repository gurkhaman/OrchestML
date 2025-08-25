from fastapi import FastAPI, HTTPException, status
from datetime import datetime
from pydantic import BaseModel
from vectorstore import VectorStoreManager
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup phase
    print("Repository service starting up...")
    try:
        print("Initializing vector store...")
        initialized = vs_manager.initialize_vectorstore()
        if initialized:
            print(f"Successfully loaded existing vectorstore from {vs_manager.persist_dir}")
        else:
            print(f"No existing vectorstore found at {vs_manager.persist_dir}")
            print("Attempting to create new vectorstore from markdown files...")
            documents_loaded = vs_manager.create_new_vectorstore()
            print(f"Successfully created vectorstore with {documents_loaded} documents")
    except Exception as e:
        print(f"Warning: Vector store initialization failed: {e}")
        print("Service will start but vector store will be unavailable")

    yield  # Service runs here

    # Shutdown phase (optional cleanup)
    print("Repository service shutting down...")

app = FastAPI(title="ComposureCI Repository", version="0.1.0", lifespan=lifespan)

vs_manager = VectorStoreManager()

class SearchRequest(BaseModel):
    query: str
    k: int = 4

class SearchResult(BaseModel):
    content: str
    metadata: dict

class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total_results: int

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

@app.post("/api/v1/vector-store/search", response_model=SearchResponse)
async def search_services(request: SearchRequest):
    if not request.query.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Query cannot be empty"
        )
    
    if not vs_manager.vectorstore:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Vector store not initialized. Please check service startup logs for initialization errors."
        )
    
    try:
        docs = vs_manager.search(request.query, k=request.k)
        
        results = [
            SearchResult(
                content=doc.page_content,
                metadata=doc.metadata
            )
            for doc in docs
        ]
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results)
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True)