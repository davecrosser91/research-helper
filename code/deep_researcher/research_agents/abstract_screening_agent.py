from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import json
import logging
from enum import Enum
from dataclasses import dataclass
from agents import FunctionTool, Agent
import asyncio
from openai import OpenAI
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

from .types import ScreenedPaper

INSTRUCTIONS = """
You are an Abstract Screening specialist focused on evaluating research papers.
Your role is to:
1. Apply inclusion/exclusion criteria to papers
2. Score relevance based on methodology, topic alignment, and impact
3. Rank papers by priority
4. Identify key themes and patterns
5. Flag papers for detailed review

Ensure thorough evaluation and clear documentation of decisions.
Focus on both individual paper assessment and pattern recognition across the corpus.
"""

class RelevanceScore(Enum):
    """Relevance scoring levels"""
    HIGH = 3
    MEDIUM = 2
    LOW = 1
    IRRELEVANT = 0

class MethodologyType(Enum):
    """Types of research methodologies"""
    EXPERIMENTAL = "experimental"
    THEORETICAL = "theoretical"
    REVIEW = "review"
    CASE_STUDY = "case_study"
    SURVEY = "survey"
    META_ANALYSIS = "meta_analysis"
    OTHER = "other"

class ScreeningCriteria(BaseModel):
    """Criteria for screening papers"""
    min_date: Optional[datetime] = None
    max_date: Optional[datetime] = None
    required_keywords: List[str] = Field(default_factory=list)
    excluded_keywords: List[str] = Field(default_factory=list)
    methodology_types: List[MethodologyType] = Field(default_factory=list)
    min_relevance_score: RelevanceScore = Field(default=RelevanceScore.LOW)
    custom_criteria: Dict[str, Any] = Field(default_factory=dict)

class ThemeIdentification(BaseModel):
    """Theme identification in papers"""
    theme_name: str
    keywords: List[str]
    frequency: int
    papers: List[str]  # List of paper IDs
    confidence: float

class ScreeningResult(BaseModel):
    """Structure for paper screening results."""
    relevance_score: float = Field(
        ..., 
        ge=0, 
        le=1, 
        description="Relevance score between 0 and 1",
        default_factory=lambda: 0.0
    )
    inclusion_criteria: Dict[str, bool] = Field(
        description="Results for each inclusion criterion",
        default_factory=lambda: {
            "criterion1": False,
            "criterion2": False,
            "criterion3": False
        }
    )
    priority_rank: int = Field(
        ..., 
        ge=1, 
        description="Priority ranking (1 being highest)",
        default_factory=lambda: 1
    )
    rationale: str = Field(
        description="Explanation for the screening decision",
        default_factory=lambda: ""
    )

class ScreeningBatch(BaseModel):
    """Batch of screening results"""
    batch_id: str
    papers: List[ScreeningResult]
    batch_themes: List[ThemeIdentification]
    batch_statistics: Dict[str, Any]
    timestamp: datetime

class AbstractScreeningAgent:
    """Agent for screening paper abstracts based on research criteria."""
    
    def __init__(self, client: OpenAI = None, timeout: int = 120):
        self.client = client or OpenAI()
        self.timeout = timeout
        
    async def screen_paper(self, paper: Dict[str, Any], criteria: Dict[str, Any], context: Dict[str, Any] = None) -> ScreenedPaper:
        """Screen a single paper based on its abstract and metadata."""
        try:
            # Create the system message with instructions
            system_message = """You are an expert at screening research papers for systematic reviews. Your role is to:
            1. Analyze paper abstracts against inclusion criteria
            2. Assess relevance to the research question
            3. Evaluate methodological quality
            4. Assign priority rankings
            5. Provide clear rationale for decisions
            
            You must output your response in the following JSON format:
            {
                "relevance_score": float between 0 and 1,
                "inclusion_criteria": {
                    "criterion1": boolean,
                    "criterion2": boolean,
                    "criterion3": boolean,
                },
                "priority_rank": integer (1 being highest),
                "rationale": "explanation string"
            }"""
            
            # Create the user message with the paper and criteria
            user_message = f"""Please screen this paper against the given criteria:
            
            Title: {paper.get('title', 'N/A')}
            Authors: {', '.join(paper.get('authors', ['N/A']))}
            Abstract: {paper.get('abstract', 'N/A')}
            
            Research Context: {json.dumps(context) if context else '{}'}
            Screening Criteria: {json.dumps(criteria)}
            
            Provide a detailed assessment of the paper's relevance and quality."""
            
            # Call the OpenAI API with a timeout
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat.completions.create,
                        model="gpt-4o-mini",
                        response_format={"type": "json_object"},
                        messages=[
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": user_message}
                        ]
                    ),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                raise TimeoutError("Assistant took too long to respond")
            
            # Parse the response
            try:
                response_data = json.loads(response.choices[0].message.content)
                screening_result = ScreeningResult(**response_data)
                
                # Convert to ScreenedPaper format
                return ScreenedPaper(
                    paper_id=paper.get('paper_id', ''),
                    title=paper.get('title', ''),
                    authors=paper.get('authors', []),
                    abstract=paper.get('abstract', ''),
                    relevance_score=screening_result.relevance_score,
                    inclusion_criteria=screening_result.inclusion_criteria,
                    priority_rank=screening_result.priority_rank,
                    metadata={
                        "rationale": screening_result.rationale,
                        **paper.get('metadata', {})
                    }
                )
                
            except (json.JSONDecodeError, KeyError) as e:
                raise ValueError(f"Invalid response format: {str(e)}")
            
        except TimeoutError:
            raise  # Re-raise TimeoutError without wrapping
        except Exception as e:
            raise RuntimeError(f"Failed to screen paper: {str(e)}") from e
            
    async def screen_papers(self, papers: List[Dict[str, Any]], criteria: Dict[str, Any], context: Dict[str, Any] = None) -> List[ScreenedPaper]:
        """Screen multiple papers in parallel."""
        tasks = [
            self.screen_paper(paper, criteria, context)
            for paper in papers
        ]
        return await asyncio.gather(*tasks)

# Create the abstract screening agent
abstract_screening_agent = Agent(
    name="Abstract Screening Agent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
) 