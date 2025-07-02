from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum

class QuestionType(str, Enum):
    FACTUAL = "factual"
    HYPOTHESIS = "hypothesis"
    METHODOLOGY = "methodology"
    COMPARATIVE = "comparative"

class SophiaOutput(BaseModel):
    question_type: QuestionType
    keywords: List[str]

class EvidenceItem(BaseModel):
    title: str
    doi: Optional[str] = None
    summary: str
    url: str
    authors: List[str] = []
    source: str  # "arxiv" or "pubmed"

class CriticFeedback(BaseModel):
    """Feedback from Critic agent for evidence quality assessment."""
    should_rerun: bool = False
    rerun_reason: Optional[str] = None
    quality_score: float = 1.0
    suggestions: List[str] = []

class NovaOutput(BaseModel):
    evidence: List[EvidenceItem]
    critic_feedback: Optional[CriticFeedback] = None

class RoadmapItem(BaseModel):
    priority: int
    research_area: str
    next_milestone: str
    timeline: str
    success_probability: float

class Citation(BaseModel):
    doi: str
    title: str
    idx: int

class CriticOutput(BaseModel):
    passes: bool
    missing_points: List[str]
    support_level: str = "weak"

class LyraOutput(BaseModel):
    answer: str
    gaps: List[str]
    roadmap: List[RoadmapItem]
    citations: List[Citation]
    critic_feedback: Optional[CriticOutput] = None

class NumericalFinding(BaseModel):
    percentages: List[str] = []
    p_values: List[str] = []
    confidence_intervals: List[str] = []
    sample_sizes: List[str] = []
    effect_sizes: List[str] = []
    statistical_tests: List[str] = []

class AskRequest(BaseModel):
    question: str

class AskResponse(BaseModel):
    task_id: str

class TaskStatus(str, Enum):
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskResult(BaseModel):
    task_id: str
    status: TaskStatus
    question: str
    sophia_output: Optional[SophiaOutput] = None
    nova_output: Optional[NovaOutput] = None
    numerical_findings: Optional[List[NumericalFinding]] = None
    lyra_output: Optional[LyraOutput] = None
    critic_output: Optional[CriticOutput] = None
    error: Optional[str] = None

class FeedbackRequest(BaseModel):
    task_id: str
    rating: int  # 1-5 scale
    comment: Optional[str] = None
    user_email: Optional[str] = None

class FeedbackResponse(BaseModel):
    status: str
    message: str 