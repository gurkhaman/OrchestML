"""
Pydantic models for ComposureCI orchestrator service.
Defines structured schemas for LLM responses and API contracts.
"""

from pydantic import BaseModel, Field, ConfigDict
from typing import Any

class TaskArgs(BaseModel):
    """Task execution parameters."""
    model_config = ConfigDict(extra="forbid")
    image:str | None = None
    text:str | None = None
    document: str | None = None

class Task(BaseModel):
    """Individual task/service definition"""
    task: str = Field(description="Service or task name")
    service_name: str = Field(description="Service name")
    id : int = Field(description="Unique task identifier")
    dep: list[int] = Field(description="Task dependencies, [-1] for no dependencies") # TODO: What happens if the field is optional?
    args: TaskArgs = Field(description="Task execution parameters")
    model_config = ConfigDict(extra="forbid")

class CompositionBlueprint(BaseModel):
    """Single composition blueprint containing multiple tasks"""
    tasks: list[Task] = Field(description="Task execution sequence")
    description: str | None = Field(default=None, description="Composition blueprint summary")
    model_config = ConfigDict(extra="forbid")

class CompositionBlueprintAgentResponse(BaseModel):
    """Multiple composition blueprints alternatives for a user request."""
    alternatives: list[CompositionBlueprint] = Field(description="Composition blueprints alternatives")
    model_config = ConfigDict(extra="forbid")

class CompositionConfirmation(BaseModel):
    """Confirmation data for deploying a composition."""
    confirmed_blueprint: CompositionBlueprint = Field(description="The selected blueprint to deploy")
    deployment_context: dict[str, Any] = Field(description="Deployment configuration and context")
    original_requirements: str = Field(description="Original user requirements")
    selected_alternative: int = Field(description="Index of selected alternative")
    confirmed_at: str = Field(description="ISO timestamp of confirmation")
    model_config = ConfigDict(extra="forbid")

class CompositionConfirmationResponse(BaseModel):
    """Response after confirming a composition deployment."""
    composition_id: str = Field(description="UUID of the confirmed composition")
    status: str = Field(description="Confirmation status")
    confirmed_at: str = Field(description="ISO timestamp of confirmation")
    deployment_context: dict[str, Any] = Field(description="Stored deployment context")
    model_config = ConfigDict(extra="forbid")

class RecompositionTrigger(BaseModel):
    """Trigger for recomposing a failed composition."""
    composition_id: str = Field(description="UUID of the original composition")
    trigger_type: str = Field(description="Type of trigger (e.g., performance_degradation)")
    failure_evidence: dict[str, Any] = Field(description="Performance metrics and failure data")
    failure_analysis: str = Field(description="Description of what failed")
    timestamp: str = Field(description="ISO timestamp of the trigger")
    model_config = ConfigDict(extra="forbid")

class RecompositionResponse(BaseModel):
    """Response after triggering recomposition."""
    original_composition_id: str = Field(description="UUID of the original composition")
    new_composition_id: str = Field(description="UUID of the new recomposed solution")
    status: str = Field(description="Recomposition status")
    blueprints: CompositionBlueprintAgentResponse = Field(description="New composition alternatives")
    recomposition_reasoning: str = Field(description="Explanation of changes made")
    created_at: str = Field(description="ISO timestamp of recomposition")
    model_config = ConfigDict(extra="forbid")

class CompositionStatus(BaseModel):
    """Status information for a composition."""
    composition_id: str = Field(description="UUID of the composition")
    status: str = Field(description="Current status (e.g., created, confirmed, deployed, failed)")
    created_at: str = Field(description="ISO timestamp of creation")
    confirmed_at: str | None = Field(default=None, description="ISO timestamp of confirmation")
    deployment_context: dict[str, Any] | None = Field(default=None, description="Deployment configuration")
    model_config = ConfigDict(extra="forbid")
