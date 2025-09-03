from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
from typing import Any
import uuid
import httpx
import yaml
from pathlib import Path
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from dotenv import dotenv_values
from models import Task, CompositionBlueprint, CompositionBlueprintAgentResponse
from langchain_ollama import ChatOllama
import os


config = dotenv_values(".env")
REPOSITORY_URL = "http://repository:8001"
os.environ["LANGCHAIN_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = config.get("LANGCHAIN_API_KEY")


def create_llm():
    """Create LLM instance based on provider configuration"""
    provider = config.get("LLM_PROVIDER", "openai").lower()
    provider = "openai"

    print(f"Creating LLM instance for {provider}")
    if provider == "ollama":
        return ChatOllama(
            base_url=f"http://{config.get('OLLAMA_URL')}",
            model=config.get("OLLAMA_MODEL"),
            temperature=0,
        ).bind_tools([CompositionBlueprintAgentResponse])
    else:
        return ChatOpenAI(
            model=config.get("LLM_MODEL", "gpt-5-2025-08-07"),
            temperature=0, 
            api_key=config.get("OPENAI_API_KEY")
        )

llm = create_llm()

# Load prompts from YAML
def load_prompts():
    prompts_path = Path(__file__).parent / "prompts.yaml"
    with open(prompts_path, 'r') as f:
        return yaml.safe_load(f)

prompts = load_prompts()

app = FastAPI(title="ComposureCI Orchestrator", version="0.1.0")

class ComposeRequest(BaseModel):
    requirements: str
    constraints: dict[str, Any] = {}

class ComposeResponse(BaseModel):
    composition_id: str
    status: str
    blueprints: CompositionBlueprintAgentResponse
    created_at: str

class RAGRequest(BaseModel):
    question: str
    prompt_name: str = "simple_composition"
    template: str | None = None
    
compositions = {}

# RAG chain functions
async def retrieve_services(query: str, k: int = 4) -> str:
    """Get context from repository service"""
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{REPOSITORY_URL}/api/v1/vector-store/search", 
                                   json={"query": query, "k": k})
        if response.status_code == 200:
            results = response.json()["results"]
            return "\n\n".join([r["content"] for r in results])
        raise Exception(f"Search failed: {response.status_code}")

async def rag_query(question: str, prompt_template: str) -> CompositionBlueprintAgentResponse:
    """Simple RAG chain"""
    context = await retrieve_services(question)
    prompt = PromptTemplate.from_template(prompt_template)

    chain = (
        {"context": lambda x: context, "question": RunnablePassthrough()}
        | prompt | llm.with_structured_output(CompositionBlueprintAgentResponse)
    )

    result = await chain.ainvoke(question)

    return result

async def get_prompt(prompt_name: str) -> str:
    """Get prompt template by name"""
    return prompts["prompts"].get(prompt_name, "")

async def compose_with_rag(requirements: str) -> CompositionBlueprintAgentResponse:
    """Get raw LLM composition breakdown response"""
    template = await get_prompt("composition_decomposition")  
    raw_response = await rag_query(requirements, template)
    return raw_response

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
    
    # Get RAG-generated composition breakdowns
    raw_breakdowns = await compose_with_rag(request.requirements)
    
    composition = {
        "composition_id": composition_id,
        "status": "success",
        "blueprints": raw_breakdowns,
        "created_at": datetime.now().isoformat(),
    }

    compositions[composition_id] = composition
    
    return ComposeResponse(**composition)

@app.get("/api/v1/compositions/{composition_id}")
async def get_composition(composition_id: str):
    if composition_id not in compositions:
        return {"error": "Composition not found"}, 404
    return compositions[composition_id]

@app.post("/api/v1/search")
async def search_repository(request: dict):
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{REPOSITORY_URL}/api/v1/vector-store/search", json=request)
            return response.json()
    except Exception as e:
        return {
            "status": "connection error",
            "message": f"Failed to connect to repository service: {str(e)}"
        }

@app.post("/api/v1/rag")
async def rag_endpoint(request: RAGRequest):
    """Test RAG chain functionality"""
    try:
        # Get template from prompts.yaml or use provided template
        if request.template:
            template = request.template
        else:
            template = await get_prompt(request.prompt_name)
            
        result = await rag_query(request.question, template)
        return {
            "status": "success",
            "question": request.question,
            "prompt_used": request.prompt_name if not request.template else "custom",
            "answer": result
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)