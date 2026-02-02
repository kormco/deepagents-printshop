"""
Shared types for the QA orchestrator pipeline.

Extracted from workflow_coordinator.py so that both the LangGraph workflow
and the coordinator can import them without circular dependencies.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class AgentType(Enum):
    """Available agent types."""
    CONTENT_EDITOR = "content_editor"
    LATEX_SPECIALIST = "latex_specialist"
    VISUAL_QA = "visual_qa"


class WorkflowStage(Enum):
    """Workflow execution stages."""
    INITIALIZATION = "initialization"
    CONTENT_REVIEW = "content_review"
    LATEX_OPTIMIZATION = "latex_optimization"
    VISUAL_QA = "visual_qa"
    QUALITY_ASSESSMENT = "quality_assessment"
    ITERATION = "iteration"
    COMPLETION = "completion"
    ESCALATION = "escalation"


@dataclass
class AgentResult:
    """Result from agent execution."""
    agent_type: AgentType
    success: bool
    version_created: str
    quality_score: Optional[float]
    processing_time: float
    issues_found: List[str]
    optimizations_applied: List[str]
    error_message: Optional[str] = None
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialize to a plain dict for state storage."""
        return {
            "agent_type": self.agent_type.value,
            "success": self.success,
            "version_created": self.version_created,
            "quality_score": self.quality_score,
            "processing_time": self.processing_time,
            "issues_found": self.issues_found,
            "optimizations_applied": self.optimizations_applied,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentResult":
        """Reconstruct an AgentResult from a dict."""
        return cls(
            agent_type=AgentType(data["agent_type"]),
            success=data["success"],
            version_created=data["version_created"],
            quality_score=data.get("quality_score"),
            processing_time=data.get("processing_time", 0.0),
            issues_found=data.get("issues_found", []),
            optimizations_applied=data.get("optimizations_applied", []),
            error_message=data.get("error_message"),
            metadata=data.get("metadata"),
        )
