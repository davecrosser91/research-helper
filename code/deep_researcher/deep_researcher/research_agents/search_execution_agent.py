from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from agents import FunctionTool, Agent
import arxiv
import json
import logging
from datetime import datetime
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

from agents import Agent, FunctionTool
from agents.model_settings import ModelSettings

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INSTRUCTIONS = """
You are a Search Execution specialist focused on thorough and systematic paper retrieval from ArXiv.
Your role is to:
1. Execute optimized searches with proper error handling
2. Retrieve and store complete paper metadata
3. Process results in efficient batches
4. Prepare raw results for the screening phase

Ensure all searches are properly logged and documented. Handle rate limits and errors gracefully.
Focus on completeness and reliability of the search results.
"""

class PaperMetadata(BaseModel):
    """Structured paper metadata for consistent processing"""
    arxiv_id: str
    title: str
    authors: List[str]
    abstract: str
    categories: List[str]
    primary_category: str
    published_date: datetime
    updated_date: Optional[datetime]
    pdf_url: str
    abstract_url: str
    journal_ref: Optional[str]
    doi: Optional[str]
    comment: Optional[str]

class SearchExecutionArgs(BaseModel):
    query: str = Field(description="The optimized search query")
    max_results: int = Field(default=100, description="Maximum number of results to process", gt=0, le=1000)
    categories: Optional[List[str]] = Field(default=None, description="ArXiv categories to filter by")
    batch_size: int = Field(default=50, description="Number of papers to process in each batch", gt=0, le=100)
    min_date: Optional[str] = Field(default=None, description="Minimum publication date (YYYY-MM-DD)")
    max_date: Optional[str] = Field(default=None, description="Maximum publication date (YYYY-MM-DD)")

    @field_validator('query')
    def query_not_empty(cls, v):
        if not v.strip():
            raise ValueError('Query cannot be empty')
        return v.strip()

    @field_validator('categories')
    def validate_categories(cls, v):
        if v is None:
            return v
        valid_categories = {
            'cs.AI', 'quant-ph', 'cs.LG', 'cs.CL', 'cs.NE',
            'stat.ML', 'cs.CV', 'cs.RO', 'cs.HC'
        }
        for category in v:
            if category not in valid_categories:
                raise ValueError(f'Invalid category: {category}. Valid categories are: {valid_categories}')
        return v

class BatchResult(BaseModel):
    """Results from processing a batch of papers"""
    batch_number: int
    papers: List[PaperMetadata]
    total_processed: int
    has_more: bool
    search_metadata: Dict[str, Any]

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True
)
async def execute_search_batch(client: arxiv.Client, search: arxiv.Search, start: int, batch_size: int) -> List[PaperMetadata]:
    """Execute a single batch of the search with retry logic"""
    logger.info(f"Processing batch starting at {start} with size {batch_size}")
    
    results = []
    search_iter = client.results(search)
    
    # Skip to the start position
    for _ in range(start):
        try:
            next(search_iter)
        except StopIteration:
            return results
    
    # Get the batch_size number of results
    for _ in range(batch_size):
        try:
            result = next(search_iter)
            paper = PaperMetadata(
                arxiv_id=result.entry_id.split('/')[-1],
                title=result.title,
                authors=[author.name for author in result.authors],
                abstract=result.summary,
                categories=result.categories,
                primary_category=result.primary_category,
                published_date=result.published,
                updated_date=result.updated,
                pdf_url=result.pdf_url,
                abstract_url=result.entry_id,
                journal_ref=result.journal_ref,
                doi=result.doi,
                comment=result.comment
            )
            results.append(paper)
        except StopIteration:
            break
    
    return results

async def search_execution(_, args_json: str) -> str:
    """Execute a complete search operation with batching and full metadata retrieval"""
    args = SearchExecutionArgs.model_validate_json(args_json)
    
    # Build the search query
    search_query = args.query
    if args.categories:
        category_query = ' OR '.join(f'cat:{cat}' for cat in args.categories)
        search_query = f'({search_query}) AND ({category_query})'
    
    # Create arxiv client
    client = arxiv.Client()
    
    # Initialize search
    search = arxiv.Search(
        query=search_query,
        max_results=args.max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    all_batches = []
    total_processed = 0
    batch_number = 1
    
    while total_processed < args.max_results:
        try:
            batch_results = await execute_search_batch(
                client,
                search,
                total_processed,
                min(args.batch_size, args.max_results - total_processed)
            )
            
            if not batch_results:
                break
                
            batch = BatchResult(
                batch_number=batch_number,
                papers=batch_results,
                total_processed=total_processed + len(batch_results),
                has_more=total_processed + len(batch_results) < args.max_results,
                search_metadata={
                    "query": args.query,
                    "categories": args.categories,
                    "batch_size": args.batch_size,
                    "timestamp": datetime.now().isoformat()
                }
            )
            
            all_batches.append(batch.model_dump())
            total_processed += len(batch_results)
            batch_number += 1
            
            logger.info(f"Completed batch {batch_number-1}, processed {total_processed} papers")
            
        except Exception as e:
            logger.error(f"Error processing batch {batch_number}: {str(e)}")
            raise
    
    return json.dumps(all_batches, default=str)

# Create the function tool
search_execution_tool = FunctionTool(
    name="search_execution",
    description="Execute complete search operations with batching, retries, and full metadata retrieval",
    params_json_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The optimized search query"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to process",
                "default": 100,
                "minimum": 1,
                "maximum": 1000
            },
            "categories": {
                "type": "array",
                "items": {"type": "string"},
                "description": "ArXiv categories to filter by"
            },
            "batch_size": {
                "type": "integer",
                "description": "Number of papers to process in each batch",
                "default": 50,
                "minimum": 1,
                "maximum": 100
            },
            "min_date": {
                "type": "string",
                "description": "Minimum publication date (YYYY-MM-DD)",
                "format": "date"
            },
            "max_date": {
                "type": "string",
                "description": "Maximum publication date (YYYY-MM-DD)",
                "format": "date"
            }
        },
        "required": ["query"],
        "additionalProperties": False
    },
    on_invoke_tool=search_execution
)

# Create the search execution agent
search_execution_agent = Agent(
    name="ArXiv Search Execution Agent",
    instructions=INSTRUCTIONS,
    model="gpt-4o-mini",
    tools=[search_execution_tool]
) 