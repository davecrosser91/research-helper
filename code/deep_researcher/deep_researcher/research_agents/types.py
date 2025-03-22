from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class WorkflowState(Enum):
    """States of the systematic review workflow."""
    INITIALIZING = "initializing"
    QUESTION_FORMULATION = "question_formulation"
    KEYWORD_ANALYSIS = "keyword_analysis"
    PAPER_SEARCH = "paper_search"
    ABSTRACT_SCREENING = "abstract_screening"
    COMPLETED = "completed"
    ERROR = "error"

class SearchStrategy(BaseModel):
    """Search strategy with keywords and constraints."""
    keywords: List[str] = Field(..., description="List of search keywords")
    combinations: List[str] = Field(..., description="Boolean combinations of keywords")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Search constraints")

# Research Question Types
class Question(BaseModel):
    """Structure for research questions."""
    question: str
    sub_questions: List[str]

class ResearchQuestion(BaseModel):
    """Complete research question with validation."""
    question: Question
    validation: Dict[str, bool]

class KeywordSet(BaseModel):
    """Keyword set for literature search."""
    primary_terms: List[str] = Field(..., description="Primary search terms")
    secondary_terms: List[str] = Field(default_factory=list, description="Secondary search terms")
    combinations: List[str] = Field(default_factory=list, description="Boolean combinations of terms")
    hit_counts: Dict[str, int] = Field(default_factory=dict, description="Number of hits per term/combination")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class PaperResult(BaseModel):
    """Structure for paper search results."""
    paper_id: str
    title: str
    abstract: str
    metadata: Dict[str, Any]

class ScreenedPaper(BaseModel):
    """Structure for screened paper results."""
    paper_id: str
    title: str
    abstract: str
    metadata: Dict[str, Any]
    relevance_score: float
    inclusion_criteria: Dict[str, bool]
    priority_rank: int

# Input/Output Types for Agents
class FormulateQuestionInput(BaseModel):
    """Input for question formulation."""
    research_area: str
    constraints: Dict[str, Any]

class FormulateQuestionOutput(BaseModel):
    """Output from question formulation."""
    question: Question
    validation: Dict[str, bool]

class KeywordAnalysisInput(BaseModel):
    """Input for keyword analysis."""
    research_question: ResearchQuestion = Field(..., description="The research question to analyze")

class KeywordAnalysisOutput(BaseModel):
    """Output from keyword analysis."""
    keywords: List[str]
    combinations: List[str]
    constraints: Dict[str, Any]

class AbstractScreeningInput(BaseModel):
    """Input for abstract screening."""
    papers: List[Dict[str, Any]] = Field(..., description="Papers to screen")
    criteria: Dict[str, Any] = Field(..., description="Screening criteria")

class AbstractScreeningOutput(BaseModel):
    """Output from abstract screening."""
    screened_papers: List[ScreenedPaper] = Field(..., description="Screened papers with results")
    summary: Dict[str, Any] = Field(..., description="Summary of screening results") 