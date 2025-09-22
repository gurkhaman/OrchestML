from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
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
from models import (
    Task, 
    CompositionBlueprint, 
    CompositionBlueprintAgentResponse,
    CompositionConfirmation,
    CompositionConfirmationResponse,
    RecompositionTrigger,
    RecompositionResponse,
    CompositionStatus
)
from langchain_ollama import ChatOllama
from composition import graph, CompositionState
import os

config = dotenv_values(".env")
REPOSITORY_URL = "http://repository:8001"
os.environ["LANGCHAIN_TRACING"] = "true"
os.environ["LANGSMITH_API_KEY"] = config.get("LANGSMITH_API_KEY")
os.environ["LANGSMITH_PROJECT"] = config.get("LANGSMITH_PROJECT")

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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"], 
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

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
confirmed_compositions = {}  # Store confirmed compositions for recomposition

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

async def compose_with_langgraph(requirements: str, constraints: dict[str, Any] = {}) -> CompositionBlueprintAgentResponse:
    """Use LangGraph composition pipeline for requirements analysis and service composition"""
    initial_state: CompositionState = {
        "requirements": requirements,
        "constraints": constraints,
        "analyzed_requirements": None,
        "requirement_cot": None,
        "structured_tasks": None,
        "task_breakdown": None,
        "retrieved_services": [],
        "task_service_candidates": None,
        "final_composition": None,
        "reasoning_steps": []
    }
    
    # Run the LangGraph pipeline
    result = await graph.ainvoke(initial_state)
    
    # Extract the final composition from the result
    final_composition = result.get("final_composition")
    
    if not final_composition:
        raise HTTPException(status_code=500, detail="LangGraph pipeline failed to generate composition")
    
    return final_composition

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
    
    # Get LangGraph-generated composition breakdowns
    raw_breakdowns = await compose_with_langgraph(request.requirements, request.constraints)
    
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

@app.post("/api/v1/compositions/{composition_id}/confirm", response_model=CompositionConfirmationResponse)
async def confirm_composition(composition_id: str, confirmation: CompositionConfirmation):
    """
    Confirm a composition for deployment and store context for potential recomposition.
    """
    # Verify the composition exists
    if composition_id not in compositions:
        raise HTTPException(status_code=404, detail="Composition not found")
    
    original_composition = compositions[composition_id]
    
    # Store the confirmed composition with full context for recomposition
    confirmed_compositions[composition_id] = {
        "composition_id": composition_id,
        "original_composition": original_composition,
        "confirmed_blueprint": confirmation.confirmed_blueprint,
        "deployment_context": confirmation.deployment_context,
        "original_requirements": confirmation.original_requirements,
        "selected_alternative": confirmation.selected_alternative,
        "confirmed_at": confirmation.confirmed_at,
        "status": "deployed"
    }
    
    # TODO: Optionally notify monitoring service about new deployment
    # await notify_monitoring_service(composition_id, confirmed_compositions[composition_id])
    
    return CompositionConfirmationResponse(
        composition_id=composition_id,
        status="confirmed",
        confirmed_at=confirmation.confirmed_at,
        deployment_context=confirmation.deployment_context
    )

@app.get("/api/v1/compositions/{composition_id}/status", response_model=CompositionStatus)
async def get_composition_status(composition_id: str):
    """
    Get the current status of a composition (created, confirmed, deployed, etc.)
    """
    # Check if it's a confirmed composition first
    if composition_id in confirmed_compositions:
        confirmed = confirmed_compositions[composition_id]
        return CompositionStatus(
            composition_id=composition_id,
            status=confirmed["status"],
            created_at=confirmed["original_composition"]["created_at"],
            confirmed_at=confirmed["confirmed_at"],
            deployment_context=confirmed["deployment_context"]
        )
    
    # Check if it's just a created composition
    if composition_id in compositions:
        composition = compositions[composition_id]
        return CompositionStatus(
            composition_id=composition_id,
            status="created",
            created_at=composition["created_at"],
            confirmed_at=None,
            deployment_context=None
        )
    
    raise HTTPException(status_code=404, detail="Composition not found")

@app.post("/api/v1/recompose", response_model=RecompositionResponse)
async def recompose_composition(trigger: RecompositionTrigger):
    """
    Generate a new composition based on failure analysis of a previous composition.
    Uses the original requirements and failure context to create improved alternatives.
    """
    # Verify the original composition exists and was confirmed
    if trigger.composition_id not in confirmed_compositions:
        raise HTTPException(
            status_code=404, 
            detail="Original composition not found or was never confirmed"
        )
    
    original_context = confirmed_compositions[trigger.composition_id]
    
    # Construct enhanced requirements that include failure context
    enhanced_requirements = f"""
    Original Requirements:
    {original_context['original_requirements']}
    
    Previous Implementation Issues:
    - Trigger: {trigger.trigger_type}
    - Failure Analysis: {trigger.failure_analysis}
    - Performance Evidence: {trigger.failure_evidence}
    
    Requirements for Improved Solution:
    - Address the identified performance issues
    - Maintain all original functional requirements
    - Optimize for better execution characteristics
    - Consider alternative service implementations
    """
    
    # Generate new composition using LangGraph with failure context
    new_composition_id = str(uuid.uuid4())
    
    try:
        # Use the same composition pipeline but with enhanced requirements
        raw_breakdowns = await compose_with_langgraph(
            enhanced_requirements, 
            original_context['deployment_context']
        )
        
        # Store the new composition
        new_composition = {
            "composition_id": new_composition_id,
            "status": "recomposed",
            "blueprints": raw_breakdowns,
            "created_at": datetime.now().isoformat(),
            "original_composition_id": trigger.composition_id,
            "recomposition_trigger": trigger.dict()
        }
        
        compositions[new_composition_id] = new_composition
        
        # Generate reasoning explanation
        reasoning = f"""
        Recomposition triggered by {trigger.trigger_type} in original composition {trigger.composition_id}.
        
        Issues identified: {trigger.failure_analysis}
        
        Improvements made:
        - Generated alternative service selections
        - Optimized task dependencies
        - Enhanced performance characteristics
        - Maintained functional requirements
        
        New composition generated with ID: {new_composition_id}
        """
        
        return RecompositionResponse(
            original_composition_id=trigger.composition_id,
            new_composition_id=new_composition_id,
            status="recomposed",
            blueprints=raw_breakdowns,
            recomposition_reasoning=reasoning,
            created_at=new_composition["created_at"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Recomposition failed: {str(e)}"
        )

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