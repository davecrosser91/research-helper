from datetime import datetime
from typing import Dict, Any, Optional, List
import logging
import json
from openai import OpenAI
from pydantic import BaseModel, Field
from tabulate import tabulate

from research_agents.types import (
    KeywordAnalysisOutput,
    WorkflowState,
    FormulateQuestionInput,
    FormulateQuestionOutput,
    SearchStrategy,
    ScreenedPaper,
    ResearchQuestion
)
from research_agents.research_question_agent import ResearchQuestionAgent
from research_agents.keyword_analysis_agent import KeywordAnalysisAgent
from research_agents.search_execution_agent import search_execution_tool
from research_agents.abstract_screening_agent import AbstractScreeningAgent, RelevanceScore
from research_agents.keyword_refinement import KeywordRefinement, RefinementConfig
from ..firebase_helper import init_firebase, push_to_firebase

class WorkflowResult(BaseModel):
    """Complete results from the systematic review workflow."""
    research_question: FormulateQuestionOutput = Field(..., description="Results from research question formulation")
    search_strategy: SearchStrategy = Field(..., description="Results from keyword analysis")
    papers: List[Dict[str, Any]] = Field(default_factory=list, description="Papers found during search")
    screened_papers: Optional[List[Dict[str, Any]]] = Field(None, description="Results from abstract screening")
    search_stats: Dict[str, Any] = Field(default_factory=dict, description="Statistics about the search results")
    refinement_results: Optional[Dict[str, Any]] = Field(None, description="Results from keyword refinement")

class SystematicReviewWorkflow:
    """Manages the systematic review workflow.
    
    The workflow consists of five main steps:
    1. Research Question Formulation: Formulates clear research questions using FINER criteria
    2. Keyword Analysis: Generates comprehensive search strategy from research questions
    3. Keyword Refinement: Optimizes keyword combinations for better search results
    4. Paper Search: Uses ArXiv to find relevant papers based on the refined strategy
    5. Abstract Screening: Evaluates papers against inclusion criteria
    """
    
    def __init__(self, openai_client: OpenAI):
        """Initialize the workflow with OpenAI client and agents."""
        self.logger = logging.getLogger("systematic_review")
        self.state = WorkflowState.INITIALIZING
        
        # Initialize Firebase
        self.db = init_firebase()
        
        # Initialize agents
        self.research_question_agent = ResearchQuestionAgent(client=openai_client)
        self.keyword_analysis_agent = KeywordAnalysisAgent(client=openai_client)
        self.abstract_agent = AbstractScreeningAgent(client=openai_client)
        
        # Initialize workflow ID
        self.workflow_id = datetime.now().strftime("%Y%m%d_%H%M%S")

    async def start_review(
        self,
        research_area: str,
        constraints: Dict[str, Any]
    ) -> WorkflowResult:
        """Start a new systematic review."""
        try:
            result = WorkflowResult()
            
            # Store workflow initialization
            push_to_firebase(
                "workflows",
                {
                    "workflow_id": self.workflow_id,
                    "research_area": research_area,
                    "constraints": constraints,
                    "state": self.state.value,
                    "start_time": datetime.now().isoformat()
                },
                doc_id=self.workflow_id
            )
            
            # Step 1: Research Question Formulation
            print("\n🤔 Step 1: Formulating Research Questions...")
            self.state = WorkflowState.QUESTION_FORMULATION
            result.research_question = await self.research_question_agent.formulate_question(research_area)
            
            # Store research question results
            push_to_firebase(
                "research_questions",
                {
                    "workflow_id": self.workflow_id,
                    "question": result.research_question.model_dump(),
                    "research_area": research_area
                }
            )
            
            # Step 2: Keyword Analysis
            print("\n🔍 Step 2: Analyzing Keywords...")
            self.state = WorkflowState.KEYWORD_ANALYSIS
            result.search_strategy = await self.keyword_analysis_agent.generate_strategy(
                result.research_question,
                constraints
            )
            
            # Store keyword analysis results
            push_to_firebase(
                "keyword_analysis",
                {
                    "workflow_id": self.workflow_id,
                    "search_strategy": result.search_strategy.model_dump(),
                    "constraints": constraints
                }
            )
            
            # Step 3: Keyword Refinement
            print("\n📊 Step 3: Refining Keywords...")
            self.state = WorkflowState.KEYWORD_REFINEMENT
            
            refinement_config = RefinementConfig(
                keywords=result.search_strategy.keywords,
                papers_per_keyword=constraints.get("max_results", 50),
                year_range=constraints.get("year_range", 3)
            )
            
            keyword_refinement = KeywordRefinement(refinement_config)
            result.search_strategy = await keyword_refinement.enhance_search_strategy(result.search_strategy)
            result.refinement_results = result.search_strategy.metadata.get("refinement_results")
            
            # Store keyword refinement results
            push_to_firebase(
                "keyword_refinement",
                {
                    "workflow_id": self.workflow_id,
                    "refined_strategy": result.search_strategy.model_dump(),
                    "refinement_results": result.refinement_results
                }
            )
            
            # Step 4: Search for papers using scored keywords
            print("\n📚 Step 4: Searching ArXiv with Scored Keywords...")
            self.state = WorkflowState.PAPER_SEARCH
            papers = []
            
            for keyword in result.search_strategy.keywords[:3]:
                print(f"Searching keyword: {keyword}")
                search_args = {
                    "query": keyword,
                    "max_results": constraints.get("max_results", 50),
                    "batch_size": constraints.get("batch_size", 50)
                }
                
                try:
                    # Execute search
                    search_results = await search_execution_tool.on_invoke_tool(None, json.dumps(search_args))
                    batches = json.loads(search_results)
                    for batch in batches:
                        papers.extend(batch["papers"])
                        
                        # Store search results batch
                        push_to_firebase(
                            "search_results",
                            {
                                "workflow_id": self.workflow_id,
                                "keyword": keyword,
                                "batch": batch
                            }
                        )
                        
                except Exception as e:
                    self.logger.error(f"Search failed for keyword: {keyword}. Error: {str(e)}")
                    continue
            
            # Deduplicate papers based on arxiv_id
            seen_papers = set()
            unique_papers = []
            for paper in papers:
                if paper["arxiv_id"] not in seen_papers:
                    seen_papers.add(paper["arxiv_id"])
                    unique_papers.append(paper)
            
            result.papers = unique_papers
            print(f"\nFound {len(result.papers)} unique papers")
            
            # Step 5: Screen abstracts
            if result.papers:
                print("\n📖 Step 5: Screening Abstracts...")
                self.state = WorkflowState.ABSTRACT_SCREENING
                
                screened_papers = await self.abstract_agent.screen_papers(result.papers)
                
                # Format and store screening results
                screening_results = [{
                    "batch_id": "batch-1",
                    "papers": [paper.model_dump() for paper in screened_papers],
                    "batch_statistics": {
                        "total_papers": len(screened_papers),
                        "high_relevance": sum(1 for p in screened_papers if p.relevance_score > 0.7),
                        "medium_relevance": sum(1 for p in screened_papers if 0.4 <= p.relevance_score <= 0.7),
                        "low_relevance": sum(1 for p in screened_papers if p.relevance_score < 0.4)
                    },
                    "timestamp": datetime.now().isoformat()
                }]
                
                result.screened_papers = screening_results
                
                # Store screening results
                push_to_firebase(
                    "screening_results",
                    {
                        "workflow_id": self.workflow_id,
                        "screening_results": screening_results
                    }
                )
            
            self.state = WorkflowState.COMPLETED
            
            # Store final workflow state
            push_to_firebase(
                "workflows",
                {
                    "workflow_id": self.workflow_id,
                    "state": self.state.value,
                    "end_time": datetime.now().isoformat(),
                    "total_papers": len(result.papers) if result.papers else 0,
                    "total_screened": len(screened_papers) if result.screened_papers else 0
                },
                doc_id=self.workflow_id
            )
            
            return result
            
        except Exception as e:
            self.state = WorkflowState.ERROR
            self.logger.error(f"Workflow error: {str(e)}")
            
            # Store error state
            push_to_firebase(
                "workflows",
                {
                    "workflow_id": self.workflow_id,
                    "state": self.state.value,
                    "error": str(e),
                    "error_time": datetime.now().isoformat()
                },
                doc_id=self.workflow_id
            )
            
            raise RuntimeError(f"Workflow failed: {str(e)}") from e
            
    def _calculate_search_stats(self, papers: List[Dict[str, Any]], strategy: SearchStrategy) -> Dict[str, Any]:
        """Calculate statistics about the search results."""
        stats = {
            "total_papers": len(papers),
            "keyword_hits": {},
            "year_distribution": {},
            "categories": {}
        }
        
        # Count keyword hits
        print(f"Papers: {papers[0]['abstract']}")

        for keyword in strategy.keywords:
            print(f"Keyword: {keyword}")
            hits = sum([1 for paper in papers if 
                      keyword.lower() in paper["title"].lower() or 
                      keyword.lower() in paper["abstract"].lower()])
            stats["keyword_hits"][keyword] = hits
            
        # Count years and categories
        for paper in papers:
            year = paper.get("published_date", "")[:4]  # Get year from published_date
            if year:
                stats["year_distribution"][year] = stats["year_distribution"].get(year, 0) + 1
            
            categories = paper.get("categories", [])
            for category in categories:
                stats["categories"][category] = stats["categories"].get(category, 0) + 1
                
        return stats
        
    def _print_search_stats(self, stats: Dict[str, Any]):
        """Print search statistics in a nice format."""
        print(f"\nFound {stats['total_papers']} papers in total")
        
        # Print keyword hits table
        keyword_table = [[keyword, hits] for keyword, hits in stats["keyword_hits"].items()]
        print("\nKeyword Hits:")
        print(tabulate(keyword_table, headers=["Keyword", "Hits"], tablefmt="grid"))
        
        # Print year distribution
        if stats["year_distribution"]:
            years = sorted(stats["year_distribution"].keys())
            year_table = [[year, stats["year_distribution"][year]] for year in years]
            print("\nYear Distribution:")
            print(tabulate(year_table, headers=["Year", "Papers"], tablefmt="grid"))
        
        # Print top categories
        if stats["categories"]:
            categories = sorted(stats["categories"].items(), key=lambda x: x[1], reverse=True)[:5]
            category_table = [[cat, count] for cat, count in categories]
            print("\nTop Categories:")
            print(tabulate(category_table, headers=["Category", "Papers"], tablefmt="grid"))