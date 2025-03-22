from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
import time

@dataclass
class ResearchQuestion:
    main_question: str
    sub_questions: List[str]
    context: Dict[str, Any]
    validation_score: float
    user_approved: bool = False

@dataclass
class SearchStrategy:
    keywords: List[str]
    combinations: List[str]
    constraints: Dict[str, Any]
    user_approved: bool = False

@dataclass
class PaperResult:
    paper_id: str
    title: str
    abstract: str
    metadata: Dict[str, Any]
    relevance_score: Optional[float] = None
    user_reviewed: bool = False

@dataclass
class WorkflowState:
    step: str
    data: Any
    timestamp: float = field(default_factory=lambda: time.time())
    modified_by_user: bool = False 