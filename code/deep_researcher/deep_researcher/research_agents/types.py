from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class WorkflowState(Enum):
    """States for the systematic review workflow."""
    INITIALIZING = auto()
    QUESTION_FORMULATION = auto()
    KEYWORD_ANALYSIS = auto()
    SEARCH_EXECUTION = auto()
    ABSTRACT_SCREENING = auto()
    REPORT_GENERATION = auto()
    COMPLETED = auto()
    ERROR = auto()

class SearchStrategy(BaseModel):
    """Search strategy with keywords and constraints."""
    keywords: List[str] = Field(..., description="List of search keywords")
    combinations: List[str] = Field(..., description="Boolean combinations of keywords")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Search constraints")

# Research Question Types
class ResearchQuestion(BaseModel):
    """Research question with validation results."""
    question: str = Field(..., description="The main research question")
    sub_questions: List[str] = Field(default_factory=list, description="Related sub-questions")
    scope: Dict[str, Any] = Field(default_factory=dict, description="Research scope parameters")

class KeywordSet(BaseModel):
    """Keyword set for literature search."""
    primary_terms: List[str] = Field(..., description="Primary search terms")
    secondary_terms: List[str] = Field(default_factory=list, description="Secondary search terms")
    combinations: List[str] = Field(default_factory=list, description="Boolean combinations of terms")
    hit_counts: Dict[str, int] = Field(default_factory=dict, description="Number of hits per term/combination")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class ScreenedPaper(BaseModel):
    """Paper with screening results."""
    paper_id: str = Field(..., description="Unique identifier for the paper")
    title: str = Field(..., description="Paper title")
    authors: List[str] = Field(..., description="List of authors")
    abstract: str = Field(..., description="Paper abstract")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance score between 0 and 1")
    inclusion_criteria: Dict[str, bool] = Field(default_factory=dict, description="Inclusion criteria results")
    priority_rank: int = Field(..., ge=1, description="Priority ranking (1 being highest)")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

# Input/Output Types for Agents
class FormulateQuestionInput(BaseModel):
    """Input for research question formulation."""
    research_area: str = Field(..., description="The research area to investigate")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Research constraints")

class FormulateQuestionOutput(BaseModel):
    """Output from research question formulation."""
    question: ResearchQuestion = Field(..., description="The formulated research question")
    validation: Dict[str, bool] = Field(..., description="Validation results against FINER criteria")

class KeywordAnalysisInput(BaseModel):
    """Input for keyword analysis."""
    research_question: ResearchQuestion = Field(..., description="The research question to analyze")

class KeywordAnalysisOutput(BaseModel):
    """Output from keyword analysis."""
    keywords: KeywordSet = Field(..., description="The generated keyword set")
    search_strategy: str = Field(..., description="Description of the search strategy")

class AbstractScreeningInput(BaseModel):
    """Input for abstract screening."""
    papers: List[Dict[str, Any]] = Field(..., description="Papers to screen")
    criteria: Dict[str, Any] = Field(..., description="Screening criteria")

class AbstractScreeningOutput(BaseModel):
    """Output from abstract screening."""
    screened_papers: List[ScreenedPaper] = Field(..., description="Screened papers with results")
    summary: Dict[str, Any] = Field(..., description="Summary of screening results") 