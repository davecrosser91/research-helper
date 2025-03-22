from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime
import json
import logging
from enum import Enum
from dataclasses import dataclass
from agents import FunctionTool, Agent

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    """Result of paper screening"""
    paper_id: str
    title: str
    relevance_score: RelevanceScore
    methodology_type: MethodologyType
    inclusion_reasons: List[str]
    exclusion_reasons: List[str]
    identified_themes: List[ThemeIdentification]
    priority_rank: int
    detailed_review_flag: bool
    screening_notes: str
    confidence_score: float

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
            
            result = ScreeningResult(
                paper_id=paper['arxiv_id'],
                title=paper['title'],
                relevance_score=relevance_score,
                methodology_type=methodology,
                inclusion_reasons=[],  # Would be populated based on specific criteria matches
                exclusion_reasons=[],  # Would be populated based on specific criteria failures
                identified_themes=[],  # Will be updated with batch themes
                priority_rank=0,  # Will be updated after batch processing
                detailed_review_flag=relevance_score in [RelevanceScore.HIGH, RelevanceScore.MEDIUM],
                screening_notes="",  # Would contain detailed screening notes
                confidence_score=0.8  # Would be calculated based on criteria matches
            )
            screening_results.append(result)
        
        # Identify themes for the batch
        batch_themes = identify_themes(batch_papers)
        
        # Update results with themes and priority ranking
        screening_results.sort(key=lambda x: x.relevance_score.value, reverse=True)
        for rank, result in enumerate(screening_results, 1):
            result.priority_rank = rank
            result.identified_themes = [theme for theme in batch_themes 
                                     if result.paper_id in theme.papers]
        
        # Create batch result
        batch = ScreeningBatch(
            batch_id=f"batch_{batch_number}",
            papers=screening_results,
            batch_themes=batch_themes,
            batch_statistics={
                "total_papers": len(screening_results),
                "high_relevance": sum(1 for r in screening_results 
                                    if r.relevance_score == RelevanceScore.HIGH),
                "medium_relevance": sum(1 for r in screening_results 
                                      if r.relevance_score == RelevanceScore.MEDIUM),
                "low_relevance": sum(1 for r in screening_results 
                                   if r.relevance_score == RelevanceScore.LOW),
                "irrelevant": sum(1 for r in screening_results 
                                if r.relevance_score == RelevanceScore.IRRELEVANT),
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

# Create the abstract screening agent
abstract_screening_agent = Agent(
    name="Abstract Screening Agent",
    instructions=INSTRUCTIONS,
    model="gpt-4-turbo",
    tools=[abstract_screening_tool]
) 