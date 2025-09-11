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
