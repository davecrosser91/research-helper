from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field

class WorkflowState(Enum):
    """States of the systematic review workflow."""
    INITIALIZING = "initializing"
    QUESTION_FORMULATION = "question_formulation"
    KEYWORD_ANALYSIS = "keyword_analysis"
    KEYWORD_REFINEMENT = "keyword_refinement"
    PAPER_SEARCH = "paper_search"
    ABSTRACT_SCREENING = "abstract_screening"
    COMPLETED = "completed"
    ERROR = "error"

class WorkflowResult(BaseModel):
    """Complete results from the systematic review workflow."""
    research_question: 'FormulateQuestionOutput' = Field(..., description="Results from research question formulation")
    search_strategy: 'SearchStrategy' = Field(..., description="Results from keyword analysis")
    papers: List[Dict[str, Any]] = Field(default_factory=list, description="Papers found during search")
    screened_papers: Optional[List[Dict[str, Any]]] = Field(None, description="Results from abstract screening")
    search_stats: Dict[str, Any] = Field(default_factory=dict, description="Statistics about the search results")
    refinement_results: Optional[Dict[str, Any]] = Field(None, description="Results from keyword refinement")

class SearchStrategy(BaseModel):
    """Search strategy with keywords and constraints."""
    keywords: List[str] = Field(default_factory=list, description="List of search keywords")
    #combinations: List[str] = Field(..., description="Boolean combinations of keywords")
    constraints: Dict[str, Any] = Field(default_factory=dict, description="Search constraints")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the search strategy")

# Research Question Types
class Question(BaseModel):
    """Structure for research questions."""
    question: str = Field(default="")
    sub_questions: List[str] = Field(default_factory=list)

class ResearchQuestion(BaseModel):
    """Complete research question with validation."""
    question: Question
    validation: Dict[str, bool] = Field(default_factory=dict)

class KeywordSet(BaseModel):
    """Keyword set for literature search."""
    primary_terms: List[str] = Field(..., description="Primary search terms")
    secondary_terms: List[str] = Field(default_factory=list, description="Secondary search terms")
    #combinations: List[str] = Field(default_factory=list, description="Boolean combinations of terms")
    hit_counts: Dict[str, int] = Field(default_factory=dict, description="Number of hits per term/combination")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

class PaperResult(BaseModel):
    """Structure for paper search results."""
    paper_id: str
    title: str
    abstract: str
    metadata: Dict[str, Any] = Field(default_factory=dict)

class ScreenedPaper(BaseModel):
    """Structure for screened paper results."""
    paper_id: str
    title: str
    abstract: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    relevance_score: float = 0.0
    inclusion_criteria: Dict[str, bool] = Field(default_factory=dict)
    priority_rank: int = 0

# Input/Output Types for Agents
class FormulateQuestionInput(BaseModel):
    """Input for question formulation."""
    research_area: str
    constraints: Dict[str, Any] = Field(default_factory=dict)

class FormulateQuestionOutput(BaseModel):
    """Output from question formulation."""
    question: Question
    validation: Dict[str, bool] = Field(default_factory=dict)

class KeywordAnalysisInput(BaseModel):
    """Input for keyword analysis."""
    research_question: ResearchQuestion = Field(..., description="The research question to analyze")

class KeywordAnalysisOutput(BaseModel):
    """Output from keyword analysis."""
    keywords: List[str] = Field(default_factory=list)
    #combinations: List[str]
    constraints: Dict[str, Any] = Field(default_factory=dict)

class AbstractScreeningInput(BaseModel):
    """Input for abstract screening."""
    papers: List[Dict[str, Any]] = Field(..., description="Papers to screen")
    criteria: Dict[str, Any] = Field(..., description="Screening criteria")

class AbstractScreeningOutput(BaseModel):
    """Output from abstract screening."""
    screened_papers: List[ScreenedPaper] = Field(..., description="Screened papers with results")
    summary: Dict[str, Any] = Field(default_factory=dict, description="Summary of screening results") 