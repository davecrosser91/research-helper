from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
import json
import logging
from datetime import datetime
from agents import FunctionTool, Agent

from .research_question_agent import research_question_agent
from .keyword_analysis_agent import keyword_analysis_agent
from .search_execution_agent import search_execution
from .abstract_screening_agent import screen_abstracts, MethodologyType, RelevanceScore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INSTRUCTIONS = """
You are a Research Workflow Orchestrator that coordinates the systematic literature review process.
Your role is to:
1. Guide the research process from user description to final paper selection
2. Ensure smooth data flow between different research agents
3. Maintain context and research focus throughout the process
4. Provide clear progress updates and final results

Focus on maintaining research quality and relevance at each step.
"""

class ResearchInput(BaseModel):
    """User input for research workflow"""
    description: str = Field(..., description="User's description of their research interest")
    field: str = Field(..., description="General field of research (e.g., 'quantum computing', 'machine learning')")
    time_range: Optional[Dict[str, str]] = Field(
        default=None,
        description="Optional time range for papers (format: {'start': 'YYYY-MM-DD', 'end': 'YYYY-MM-DD'})"
    )
    categories: Optional[List[str]] = Field(
        default=None,
        description="Optional list of arXiv categories to search in"
    )

class RelevantPaper(BaseModel):
    """Structure for relevant papers in final output"""
    title: str
    authors: List[str]
    abstract: str
    arxiv_id: str
    url: str
    relevance_score: str
    methodology: str
    themes: List[str]
    priority_rank: int
    detailed_review_recommended: bool

class ResearchOutput(BaseModel):
    """Final output of the research workflow"""
    research_question: str
    sub_questions: List[str]
    search_strategy: Dict[str, Any]
    relevant_papers: List[RelevantPaper]
    themes: List[Dict[str, Any]]
    statistics: Dict[str, Any]
    timestamp: datetime

async def execute_research_workflow(_, args_json: str) -> str:
    """Execute the complete research workflow"""
    args = ResearchInput.model_validate_json(args_json)
    logger.info("Starting research workflow")
    
    # Step 1: Generate Research Question
    logger.info("Step 1: Generating research question")
    research_question_input = {
        "description": args.description,
        "field": args.field
    }
    research_question_result = await research_question_agent.run(research_question_input)
    research_question_data = json.loads(research_question_result)
    
    # Step 2: Keyword Analysis
    logger.info("Step 2: Analyzing keywords")
    keyword_analysis_input = {
        "research_question": research_question_data["question"],
        "sub_questions": research_question_data["sub_questions"],
        "field": args.field
    }
    keyword_analysis_result = await keyword_analysis_agent.run(keyword_analysis_input)
    keyword_data = json.loads(keyword_analysis_result)
    
    # Step 3: Execute Search
    logger.info("Step 3: Executing search")
    search_query = {
        "query": keyword_data["optimized_query"],
        "max_results": 50,  # Adjustable
        "categories": args.categories if args.categories else keyword_data["recommended_categories"],
        "batch_size": 10,
        "min_date": args.time_range["start"] if args.time_range else None,
        "max_date": args.time_range["end"] if args.time_range else None
    }
    search_results = await search_execution(None, json.dumps(search_query))
    search_data = json.loads(search_results)
    
    # Extract papers from search results
    papers = []
    for batch in search_data:
        papers.extend(batch["papers"])
    
    # Step 4: Screen Abstracts
    logger.info("Step 4: Screening abstracts")
    screening_query = {
        "papers": papers,
        "criteria": {
            "required_keywords": keyword_data["primary_keywords"],
            "excluded_keywords": keyword_data.get("excluded_keywords", []),
            "methodology_types": [
                MethodologyType.EXPERIMENTAL.value,
                MethodologyType.THEORETICAL.value,
                MethodologyType.REVIEW.value
            ],
            "min_relevance_score": RelevanceScore.MEDIUM.value,
            "custom_criteria": {
                "research_question": research_question_data["question"],
                "sub_questions": research_question_data["sub_questions"]
            }
        },
        "batch_size": 10,
        "min_confidence": 0.7
    }
    screening_results = await screen_abstracts(None, json.dumps(screening_query))
    screening_data = json.loads(screening_results)
    
    # Process results into final output format
    relevant_papers = []
    all_themes = []
    total_papers = 0
    high_relevance = 0
    medium_relevance = 0
    
    for batch in screening_data:
        # Collect themes
        all_themes.extend(batch["batch_themes"])
        
        # Process papers
        for paper in batch["papers"]:
            if paper["relevance_score"] in ["RelevanceScore.HIGH", "RelevanceScore.MEDIUM"]:
                relevant_papers.append(RelevantPaper(
                    title=paper["title"],
                    authors=papers[total_papers]["authors"],  # From original search data
                    abstract=papers[total_papers]["abstract"],
                    arxiv_id=paper["paper_id"],
                    url=f"https://arxiv.org/abs/{paper['paper_id']}",
                    relevance_score=paper["relevance_score"],
                    methodology=paper["methodology_type"],
                    themes=[theme["theme_name"] for theme in paper["identified_themes"]],
                    priority_rank=paper["priority_rank"],
                    detailed_review_recommended=paper["detailed_review_flag"]
                ))
                
                # Update statistics
                if paper["relevance_score"] == "RelevanceScore.HIGH":
                    high_relevance += 1
                else:
                    medium_relevance += 1
            
            total_papers += 1
    
    # Prepare final output
    output = ResearchOutput(
        research_question=research_question_data["question"],
        sub_questions=research_question_data["sub_questions"],
        search_strategy={
            "keywords": keyword_data,
            "query": search_query["query"],
            "categories": search_query["categories"]
        },
        relevant_papers=sorted(relevant_papers, key=lambda x: x.priority_rank),
        themes=[theme for theme in all_themes if theme["frequency"] > 2],  # Filter significant themes
        statistics={
            "total_papers_found": total_papers,
            "relevant_papers": len(relevant_papers),
            "high_relevance": high_relevance,
            "medium_relevance": medium_relevance,
            "top_themes": [theme["theme_name"] for theme in sorted(all_themes, key=lambda x: x["frequency"], reverse=True)[:5]]
        },
        timestamp=datetime.now()
    )
    
    logger.info("Research workflow completed successfully")
    return output.model_dump_json()

# Create the function tool
workflow_tool = FunctionTool(
    name="execute_research_workflow",
    description="Execute complete research workflow from user description to relevant papers",
    params_json_schema={
        "type": "object",
        "properties": {
            "description": {
                "type": "string",
                "description": "User's description of their research interest"
            },
            "field": {
                "type": "string",
                "description": "General field of research"
            },
            "time_range": {
                "type": "object",
                "properties": {
                    "start": {"type": "string", "format": "date"},
                    "end": {"type": "string", "format": "date"}
                }
            },
            "categories": {
                "type": "array",
                "items": {"type": "string"}
            }
        },
        "required": ["description", "field"]
    },
    on_invoke_tool=execute_research_workflow
)

# Create the workflow orchestrator agent
workflow_orchestrator = Agent(
    name="Research Workflow Orchestrator",
    instructions=INSTRUCTIONS,
    model="gpt-4-turbo",
    tools=[workflow_tool]
) 