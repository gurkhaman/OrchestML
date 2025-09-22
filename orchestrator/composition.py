from typing import TypedDict, Annotated, cast
from typing import Any
from pathlib import Path
import operator

from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field, ConfigDict
from models import CompositionBlueprintAgentResponse
from dotenv import dotenv_values
from langchain_core.messages import HumanMessage
from langchain_core.prompts import PromptTemplate
from langchain_ollama import ChatOllama
from langgraph.graph import StateGraph, START, END
from langgraph.constants import Send
import os
import yaml
import asyncio
import httpx

config = dotenv_values(".env")
# llm = ChatOllama(model="deepseek-r1:14b", base_url=f"http://{config.get('OLLAMA_URL')}")
llm = ChatOpenAI(model="gpt-5-nano", api_key=config.get("OPENAI_API_KEY", ""), disable_streaming=True)  # type: ignore
os.environ["LANGCHAIN_TRACING"] = "true"
langsmith_key = config.get("LANGSMITH_API_KEY")
if langsmith_key:
    os.environ["LANGSMITH_API_KEY"] = langsmith_key

# Repository service configuration
REPOSITORY_URL = "http://localhost:8001"

class RequirementAnalysisResult(BaseModel):
    """Final structured analysis based on CoT reasoning"""
    domain: str = Field(
        description="Primary domain: image-processing, text-analysis, data - transformation, multimodal, other")
    goals: list[str] = Field(description="Specific achievable goals")
    input_types: list[str] = Field(description="Required input types")
    success_criteria: list[str] = Field(description="Measurable success conditions")
    constraints: list[str] = Field(description="Limitations and preferences")
    confidence_score: int = Field(description="Confidence in analysis (1-10 scale)", ge=1, le=10)
    model_config = ConfigDict(extra="forbid")


class TaskServiceCandidate(BaseModel):
    """Task to service mapping candidate"""
    task_id: int = Field(description="Sequential task identifier (will be auto-generated)")
    task_description: str = Field(description="Clear description of what this task accomplishes")
    service_name: str = Field(description="Name of the candidate ML service from repository")
    relevance_score: int = Field(
        description="How well service capabilities match task requirements (1-10): 1=poor match, 5=moderate match, 10=perfect match",
        ge=1, le=10
    )
    confidence: int = Field(
        description="Certainty about this relevance assessment (1-10): 1=very uncertain, 5=moderate certainty, 10=completely certain",
        ge=1, le=10
    )
    model_config = ConfigDict(extra="forbid")


class TaskDescription(BaseModel):
    """Individual ML task description for structured output"""
    task_id: int = Field(description="Sequential task identifier (auto-generated)")
    name: str = Field(description="Brief task name (e.g., 'Image Deblurring')")
    description: str = Field(description="Detailed task description for repository search")
    ml_keywords: list[str] = Field(description="3-5 ML keywords for search optimization")
    model_config = ConfigDict(extra="forbid")


class TaskDecompositionResult(BaseModel):
    """Structured result from task decomposition with clean task data"""
    tasks: list[TaskDescription] = Field(description="List of atomic ML tasks")
    reasoning_summary: str = Field(description="Brief summary of decomposition logic")
    model_config = ConfigDict(extra="forbid")


class TaskRetrievalState(TypedDict):
    """State for individual task service retrieval in Send() operations"""
    task: TaskDescription


class CompositionState(TypedDict):
    # Input
    requirements: str
    constraints: dict[str, Any]

    # Step 1: Requirement Analysis
    analyzed_requirements: RequirementAnalysisResult | None
    requirement_cot: str | None

    # Step 2: Task Breakdown
    structured_tasks: list[TaskDescription] | None
    task_breakdown: str | None

    # Step 3: Composition Builder (parallel service discovery + mapping)  
    retrieved_services: Annotated[list[str], operator.add]
    task_service_candidates: list[TaskServiceCandidate] | None
    final_composition: CompositionBlueprintAgentResponse | None

    # Tracking
    reasoning_steps: list[str]


def load_prompts():
    """Load prompts from YAML file"""
    prompts_path = Path(__file__).parent / "prompts.yaml"
    with open(prompts_path, 'r') as f:
        return yaml.safe_load(f)


async def analyze_requirements(state: CompositionState) -> dict[str, Any]:
    """
    Analyze requirements using hybrid approach:
    1. Chain-of-thought reasoning (rich text)
    2. Structured final analysis (Pydantic)
    """

    # Load prompts using asyncio.to_thread to avoid blocking I/O
    prompts = await asyncio.to_thread(load_prompts)
    cot_prompt = prompts["prompts"]["requirement_cot"]
    analysis_prompt = prompts["prompts"]["requirement_analysis"]

    print("=== STAGE 1: Chain-of-Thought Reasoning ===")

    # Stage 1: Text-based chain-of-thought reasoning
    cot_formatted = cot_prompt.format(
        requirements=state["requirements"],
        constraints=state.get("constraints", {})
    )

    cot_response = await llm.ainvoke([HumanMessage(content=cot_formatted)])
    reasoning_text = cot_response.content

    print("✅ CoT Reasoning completed")
    print(f"Length: {len(reasoning_text)} characters")

    print("\n=== STAGE 2: Structured Analysis ===")

    # Stage 2: Structured analysis based on reasoning
    try:
        analysis_llm = llm.with_structured_output(RequirementAnalysisResult)

        analysis_formatted = analysis_prompt.format(
            reasoning=reasoning_text
        )

        analysis = await analysis_llm.ainvoke([HumanMessage(content=analysis_formatted)])

        print("✅ Structured analysis completed")
        print(f"Domain: {getattr(analysis, 'domain', 'unknown')}")
        print(f"Goals: {len(getattr(analysis, 'goals', []))} identified")
        print(f"Confidence: {getattr(analysis, 'confidence_score', 0)}/10")

        # Create comprehensive reasoning summary
        domain = getattr(analysis, 'domain', 'unknown')
        goals = getattr(analysis, 'goals', [])
        confidence = getattr(analysis, 'confidence_score', 0)
        reasoning_summary = f"CoT Analysis - Domain: {domain}, Goals: {len(goals)}, Confidence: {confidence}/10"

    except Exception as e:
        print(f"❌ Structured output failed: {e}")
        print("Falling back to text-only analysis")

        # Fallback to text-only analysis
        analysis = None
        reasoning_summary = "CoT Analysis completed - structured parsing failed, using text reasoning"

    print("=" * 60)

    return {
        "analyzed_requirements": analysis,  # Structured (or None if failed)
        "requirement_cot": reasoning_text,  # Rich text reasoning
        "reasoning_steps": [reasoning_summary]
    }


async def decompose_tasks(state: CompositionState) -> dict[str, Any]:
    """
    Decompose requirements into tasks using structured output
    Following hybrid CoT + structured output pattern
    """

    # Load prompts using asyncio.to_thread to avoid blocking I/O
    prompts = await asyncio.to_thread(load_prompts)
    cot_prompt = prompts["prompts"]["task_decomposition_cot"]
    extraction_prompt = prompts["prompts"]["task_structured_extraction"]

    print("=== STAGE 1: Task Decomposition CoT ===")

    # Stage 1: Task decomposition reasoning
    analyzed_requirements = state["analyzed_requirements"]
    requirement_cot = state["requirement_cot"]

    if not analyzed_requirements:
        print("❌ No structured requirements available")
        return {
            "task_breakdown": None,
            "structured_tasks": None,
            "retrieved_services": [],
            "task_service_candidates": None,
            "reasoning_steps": ["Task decomposition failed - no structured requirements"]
        }

    # Format structured analysis for prompt
    # TODO: Move this to the place where the structured analysis is actually created
    cot_formatted = cot_prompt.format(
        domain=getattr(analyzed_requirements, 'domain', 'unknown'),
        goals=str(getattr(analyzed_requirements, 'goals', [])),
        input_types=str(getattr(analyzed_requirements, 'input_types', [])),
        success_criteria=str(getattr(analyzed_requirements, 'success_criteria', [])),
        constraints=str(getattr(analyzed_requirements, 'constraints', [])),
        requirement_cot=requirement_cot or ""
    )

    cot_response = await llm.ainvoke([HumanMessage(content=cot_formatted)])
    task_breakdown_text = str(cot_response.content)

    print("✅ Task decomposition completed")
    print(f"Length: {len(task_breakdown_text)} characters")

    print("\n=== STAGE 2: Structured Task Extraction ===")

    # Stage 2: Extract structured tasks from the reasoning
    try:
        # Create a model that excludes task_id for LLM generation
        class TaskDescriptionForLLM(BaseModel):
            name: str = Field(description="Brief task name (e.g., 'Image Deblurring')")
            description: str = Field(description="Detailed task description for repository search")
            ml_keywords: list[str] = Field(description="3-5 ML keywords for search optimization")
            model_config = ConfigDict(extra="forbid")

        class TaskExtractionResult(BaseModel):
            tasks: list[TaskDescriptionForLLM] = Field(description="List of atomic ML tasks")
            reasoning_summary: str = Field(description="Brief summary of decomposition logic")
            model_config = ConfigDict(extra="forbid")

        extraction_llm = llm.with_structured_output(TaskExtractionResult)

        extraction_formatted = extraction_prompt.format(
            task_breakdown=task_breakdown_text
        )

        extraction_result = await extraction_llm.ainvoke([HumanMessage(content=extraction_formatted)])

        # Add auto-generated task_ids to create final TaskDescription objects
        structured_tasks = []
        tasks_list = getattr(extraction_result, 'tasks', [])
        for i, task in enumerate(tasks_list):
            structured_tasks.append(TaskDescription(
                task_id=i + 1,  # Auto-generate sequential IDs starting from 1
                name=getattr(task, 'name', f'Task {i+1}'),
                description=getattr(task, 'description', ''),
                ml_keywords=getattr(task, 'ml_keywords', [])
            ))

        print("✅ Structured task extraction completed")
        print(f"Extracted {len(structured_tasks)} structured tasks")

        reasoning_summary = f"Task Decomposition - {len(structured_tasks)} structured tasks extracted"

    except Exception as e:
        print(f"❌ Structured extraction failed: {e}")
        structured_tasks = None
        reasoning_summary = "Task Decomposition completed - structured extraction failed, using text analysis only"

    print("=" * 60)

    return {
        "task_breakdown": task_breakdown_text,
        "structured_tasks": structured_tasks,
        "retrieved_services": [],  # Will be populated by parallel retrieval
        "task_service_candidates": None,  # Will be handled by composition builder
        "reasoning_steps": [reasoning_summary]
    }


async def retrieve_task_services(state: TaskRetrievalState) -> dict[str, Any]:
    """Pure service retrieval - just get raw services from repository"""
    task = state["task"]

    print(f"🔍 Retrieving services for Task {task.task_id}: {task.name}")

    try:
        # Build search query from task description and keywords
        search_terms = [task.description]
        search_terms.extend(task.ml_keywords)
        query = " ".join(search_terms)

        # Repository call
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{REPOSITORY_URL}/api/v1/vector-store/search",
                                        json={"query": query, "k": 3})

            if response.status_code == 200:
                results = response.json()["results"]
                print(f"✅ Task {task.task_id}: Retrieved {len(results)} services from repository")

                # Build individual service entries with task context
                individual_services = []
                for i, result in enumerate(results):
                    metadata = result.get("metadata", {})
                    source_path = metadata.get("source", "")
                    service_name = source_path.split("/")[-1].replace(".md", "") if source_path else f"unknown-{i}"
                    
                    # Create individual service entry with full context
                    service_entry = f"""TASK {task.task_id}: {task.name}
QUERY: {query}

SERVICE: {service_name}
{result['content']}"""
                    
                    individual_services.append(service_entry)
                
                print(f"✅ Task {task.task_id}: Formatted {len(individual_services)} individual services with task context")
                
                # Return individual services for proper pooling
                return {"retrieved_services": individual_services}
            else:
                print(f"❌ Task {task.task_id}: Repository request failed: {response.status_code}")
                return {"retrieved_services": []}
        
    except Exception as e:
        print(f"❌ Task {task.task_id} service retrieval failed: {e}")
        return {"retrieved_services": []}


async def build_composition(state: CompositionState) -> dict[str, Any]:
    """
    Build final composition blueprint using hybrid CoT + structured approach
    Following the established pattern from requirements and task analysis
    """
    
    # Load prompts using asyncio.to_thread to avoid blocking I/O
    prompts = await asyncio.to_thread(load_prompts)
    cot_prompt = prompts["prompts"]["composition_builder_cot"]
    structured_prompt = prompts["prompts"]["composition_builder_structured"]
    
    print("=== STAGE 1: Composition Analysis CoT ===")
    
    # Get required data from state
    requirements = state["requirements"]
    structured_tasks = state["structured_tasks"]
    retrieved_services = state["retrieved_services"]
    
    if not structured_tasks or not retrieved_services:
        print("❌ Missing required data for composition building")
        return {
            "final_composition": None,
            "reasoning_steps": ["Composition building failed - missing tasks or services"]
        }
    
    # Format tasks for prompt
    tasks_text = ""
    for task in structured_tasks:
        tasks_text += f"Task {task.task_id}: {task.name}\nDescription: {task.description}\nKeywords: {', '.join(task.ml_keywords)}\n\n"
    
    # Format services for prompt (they're already formatted with task context)
    services_text = "\n\n".join(retrieved_services)
    
    # Stage 1: Chain-of-thought composition analysis
    cot_formatted = cot_prompt.format(
        requirements=requirements,
        structured_tasks=tasks_text.strip(),
        retrieved_services=services_text
    )
    
    cot_response = await llm.ainvoke([HumanMessage(content=cot_formatted)])
    composition_analysis = str(cot_response.content)
    
    print("✅ Composition analysis completed")
    print(f"Length: {len(composition_analysis)} characters")
    
    print("\n=== STAGE 2: Structured Blueprint Generation ===")
    
    # Stage 2: Generate structured composition blueprint
    try:
        composition_llm = llm.with_structured_output(CompositionBlueprintAgentResponse)
        
        structured_formatted = structured_prompt.format(
            composition_analysis=composition_analysis,
            requirements=requirements
        )
        
        final_composition = await composition_llm.ainvoke([HumanMessage(content=structured_formatted)])
        
        print("✅ Structured composition blueprint generated")
        print(f"Blueprint created successfully")
        
        reasoning_summary = "Composition building completed - blueprint generated with full analysis"
        
    except Exception as e:
        print(f"❌ Structured composition generation failed: {e}")
        final_composition = None
        reasoning_summary = "Composition building completed - structured generation failed, using analysis only"
    
    print("=" * 60)
    
    return {
        "final_composition": final_composition,
        "reasoning_steps": [reasoning_summary]
    }


def initiate_service_retrieval(state: CompositionState):
    """Route to parallel service retrieval using Send() for each structured task"""
    structured_tasks = state.get("structured_tasks")
    
    if not structured_tasks:
        print("❌ No structured tasks available for parallel retrieval")
        return END  # Use END constant, not string
    
    print(f"🚀 Initiating parallel service retrieval for {len(structured_tasks)} tasks")
    
    # Create Send() operations for each task
    return [Send("retrieve_task_services", {"task": task}) for task in structured_tasks]

# LangGraph composition pipeline
def create_composition_graph():
    """Create LangGraph StateGraph for composition pipeline with parallel service discovery"""

    # Create the graph
    graph = StateGraph(CompositionState)

    # Add nodes
    graph.add_node("analyze_requirements", analyze_requirements)
    graph.add_node("decompose_tasks", decompose_tasks)
    graph.add_node("retrieve_task_services", retrieve_task_services)
    graph.add_node("build_composition", build_composition)

    # Add edges
    graph.add_edge(START, "analyze_requirements")
    graph.add_edge("analyze_requirements", "decompose_tasks")
    
    # Conditional edge for parallel service retrieval
    graph.add_conditional_edges(
        "decompose_tasks",
        initiate_service_retrieval,
        ["retrieve_task_services", END]
    )
    
    # After parallel retrieval, build composition
    graph.add_edge("retrieve_task_services", "build_composition")
    graph.add_edge("build_composition", END)
    
    # Compile the graph
    compiled_graph = graph.compile()
    
    return compiled_graph


graph = create_composition_graph()