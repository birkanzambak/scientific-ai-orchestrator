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
    doi: str
    summary: str
    url: str

class NovaOutput(BaseModel):
    evidence: List[EvidenceItem]

class RoadmapItem(BaseModel):
    priority: int
    research_area: str
    next_milestone: str
    timeline: str
    success_probability: float

class Citation(BaseModel):
    doi: str
    idx: int

class LyraOutput(BaseModel):
    answer: str
    gaps: List[str]
    roadmap: List[RoadmapItem]
    citations: List[Citation]

class CriticOutput(BaseModel):
    passes: bool
    missing_points: List[str]

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