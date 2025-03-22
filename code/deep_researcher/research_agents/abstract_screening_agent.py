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
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance score between 0 and 1")
    inclusion_criteria: Dict[str, bool] = Field(description="Results for each inclusion criterion")
    priority_rank: int = Field(..., ge=1, description="Priority ranking (1 being highest)")
    rationale: str = Field(description="Explanation for the screening decision")

class ScreeningBatch(BaseModel):
    """Batch of screening results"""
    batch_id: str
    papers: List[ScreeningResult]
    batch_themes: List[ThemeIdentification]
    batch_statistics: Dict[str, Any]
    timestamp: datetime

class AbstractScreeningArgs(BaseModel):
    """Arguments for abstract screening"""
    papers: List[Dict[str, Any]]  # List of papers from search execution
    criteria: ScreeningCriteria
    batch_size: int = Field(default=10, gt=0, le=100)
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0)

    @field_validator('papers')
    def validate_papers(cls, v):
        if not v:
            raise ValueError('Papers list cannot be empty')
        return v

def evaluate_methodology(abstract: str) -> MethodologyType:
    """Evaluate the methodology type from the abstract"""
    methodology_keywords = {
        MethodologyType.EXPERIMENTAL: ['experiment', 'trial', 'measurement'],
        MethodologyType.THEORETICAL: ['theory', 'framework', 'model'],
        MethodologyType.REVIEW: ['review', 'survey', 'overview'],
        MethodologyType.CASE_STUDY: ['case study', 'case-study', 'case analysis'],
        MethodologyType.SURVEY: ['survey', 'questionnaire', 'interview'],
        MethodologyType.META_ANALYSIS: ['meta-analysis', 'meta analysis', 'systematic review']
    }
    
    # Count keyword occurrences for each methodology
    scores = {method: 0 for method in MethodologyType}
    abstract_lower = abstract.lower()
    
    for method, keywords in methodology_keywords.items():
        for keyword in keywords:
            if keyword in abstract_lower:
                scores[method] += 1
    
    # Return the methodology with highest score, or OTHER if no clear winner
    max_score = max(scores.values())
    if max_score == 0:
        return MethodologyType.OTHER
    
    methods_with_max = [m for m, s in scores.items() if s == max_score]
    return methods_with_max[0]

def calculate_relevance_score(paper: Dict[str, Any], criteria: ScreeningCriteria) -> RelevanceScore:
    """Calculate relevance score based on criteria"""
    score = 0
    reasons = []
    
    # Check keywords
    abstract_lower = paper['abstract'].lower()
    title_lower = paper['title'].lower()
    
    # Required keywords
    required_found = 0
    for keyword in criteria.required_keywords:
        if keyword.lower() in abstract_lower or keyword.lower() in title_lower:
            required_found += 1
    
    keyword_ratio = required_found / len(criteria.required_keywords) if criteria.required_keywords else 1
    score += keyword_ratio * 2
    
    # Excluded keywords
    for keyword in criteria.excluded_keywords:
        if keyword.lower() in abstract_lower or keyword.lower() in title_lower:
            score -= 1
    
    # Methodology match
    paper_methodology = evaluate_methodology(paper['abstract'])
    if paper_methodology in criteria.methodology_types:
        score += 1
    
    # Convert score to RelevanceScore
    if score >= 2.5:
        return RelevanceScore.HIGH
    elif score >= 1.5:
        return RelevanceScore.MEDIUM
    elif score >= 0.5:
        return RelevanceScore.LOW
    else:
        return RelevanceScore.IRRELEVANT

def identify_themes(papers: List[Dict[str, Any]]) -> List[ThemeIdentification]:
    """Identify common themes across papers"""
    # This would be enhanced with NLP techniques in a production environment
    themes = {}
    
    for paper in papers:
        # Simple keyword extraction from title and abstract
        text = f"{paper['title']} {paper['abstract']}".lower()
        words = text.split()
        
        # Count word frequencies (excluding common words)
        for word in words:
            if len(word) > 4:  # Simple filter for significant words
                if word not in themes:
                    themes[word] = {
                        'count': 1,
                        'papers': [paper['arxiv_id']],
                        'keywords': [word]
                    }
                else:
                    themes[word]['count'] += 1
                    if paper['arxiv_id'] not in themes[word]['papers']:
                        themes[word]['papers'].append(paper['arxiv_id'])
    
    # Convert to ThemeIdentification objects
    theme_objects = []
    for word, data in themes.items():
        if data['count'] > 1:  # Only include themes found in multiple papers
            theme_objects.append(ThemeIdentification(
                theme_name=word,
                keywords=data['keywords'],
                frequency=data['count'],
                papers=data['papers'],
                confidence=min(data['count'] / len(papers), 1.0)
            ))
    
    return sorted(theme_objects, key=lambda x: x.frequency, reverse=True)[:10]  # Top 10 themes

async def screen_abstracts(_, args_json: str) -> str:
    """Screen paper abstracts based on criteria"""
    args = AbstractScreeningArgs.model_validate_json(args_json)
    
    all_batches = []
    batch_number = 1
    
    # Process papers in batches
    for i in range(0, len(args.papers), args.batch_size):
        batch_papers = args.papers[i:i + args.batch_size]
        screening_results = []
        
        # Process each paper in the batch
        for paper in batch_papers:
            relevance_score = calculate_relevance_score(paper, args.criteria)
            methodology = evaluate_methodology(paper['abstract'])
            
            # Normalize relevance score to be between 0 and 1
            normalized_score = relevance_score.value / max(enum.value for enum in RelevanceScore)
            
            result = ScreeningResult(
                relevance_score=normalized_score,
                inclusion_criteria={
                    "meets_relevance_threshold": relevance_score.value >= args.criteria.min_relevance_score.value,
                    "has_required_methodology": methodology in args.criteria.methodology_types
                },
                priority_rank=1,  # Default to 1, will be updated based on sorting
                rationale=f"Relevance score: {relevance_score.name}, Methodology: {methodology.value}"
            )
            screening_results.append(result)
        
        # Sort by relevance score and update priority ranks
        screening_results.sort(key=lambda x: x.relevance_score, reverse=True)
        for rank, result in enumerate(screening_results, 1):
            result.priority_rank = rank
        
        # Identify themes for the batch
        batch_themes = identify_themes(batch_papers)
        
        # Create batch result
        batch = ScreeningBatch(
            batch_id=f"batch_{batch_number}",
            papers=screening_results,
            batch_themes=batch_themes,
            batch_statistics={
                "total_papers": len(screening_results),
                "high_relevance": sum(1 for r in screening_results 
                                    if r.relevance_score >= 0.75),
                "medium_relevance": sum(1 for r in screening_results 
                                      if 0.5 <= r.relevance_score < 0.75),
                "low_relevance": sum(1 for r in screening_results 
                                   if 0.25 <= r.relevance_score < 0.5),
                "irrelevant": sum(1 for r in screening_results 
                                if r.relevance_score < 0.25),
            },
            timestamp=datetime.now()
        )
        
        all_batches.append(batch.model_dump())
        batch_number += 1
        
        logger.info(f"Completed screening batch {batch_number-1}")
    
    return json.dumps(all_batches, default=str)

# Create the function tool
abstract_screening_tool = FunctionTool(
    name="screen_abstracts",
    description="Screen paper abstracts based on criteria and rank by relevance",
    params_json_schema={
        "type": "object",
        "properties": {
            "papers": {
                "type": "array",
                "items": {
                    "type": "object"
                },
                "description": "List of papers from search execution"
            },
            "criteria": {
                "type": "object",
                "properties": {
                    "min_date": {"type": "string", "format": "date-time"},
                    "max_date": {"type": "string", "format": "date-time"},
                    "required_keywords": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "excluded_keywords": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "methodology_types": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "min_relevance_score": {"type": "string"},
                    "custom_criteria": {"type": "object"}
                }
            },
            "batch_size": {
                "type": "integer",
                "default": 10,
                "minimum": 1,
                "maximum": 100
            },
            "min_confidence": {
                "type": "number",
                "default": 0.7,
                "minimum": 0,
                "maximum": 1
            }
        },
        "required": ["papers", "criteria"]
    },
    on_invoke_tool=screen_abstracts
)

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
                    ...
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
                        model="gpt-4-turbo-preview",
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
    model="gpt-4-turbo",
    tools=[abstract_screening_tool]
) 