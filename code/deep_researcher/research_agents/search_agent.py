from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from agents import FunctionTool, Agent
import arxiv
import json

from agents import Agent, FunctionTool
from agents.model_settings import ModelSettings

INSTRUCTIONS = (
    "You are a research assistant specialized in scientific literature. Given a search term, you search arXiv "
    "for relevant papers and produce a concise summary of the results. Focus on the most relevant and recent "
    "papers. The summary must be 2-3 paragraphs and less than 300 words. Capture the main scientific findings "
    "and methodologies. Write succinctly, focusing on key contributions and results. This will be consumed by "
    "someone synthesizing a report, so it's vital you capture the essence and ignore any peripheral details."
)

class ArxivSearchArgs(BaseModel):
    query: str = Field(description="The search query to find relevant papers")
    max_results: int = Field(default=5, description="Maximum number of results to return", gt=0, le=100)
    categories: Optional[List[str]] = Field(default=None, description="List of arXiv categories to filter by (e.g. 'cs.AI' for Artificial Intelligence, 'quant-ph' for Quantum Physics)")

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

async def arxiv_search(_, args_json: str) -> str:
    """Search arXiv for papers matching the query and return formatted results."""
    args = ArxivSearchArgs.model_validate_json(args_json)
    
    # Build the search query
    search_query = args.query
    if args.categories:
        category_query = ' OR '.join(f'cat:{cat}' for cat in args.categories)
        search_query = f'({search_query}) AND ({category_query})'
    
    # Create arxiv client
    client = arxiv.Client()
    
    # Perform the search
    search = arxiv.Search(
        query=search_query,
        max_results=args.max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    # Format results
    results = []
    for result in client.results(search):
        paper_info = {
            'Title': result.title,
            'Authors': ', '.join(author.name for author in result.authors),
            'Summary': result.summary,
            'ArXiv ID': result.entry_id.split('/')[-1],
            'URL': result.pdf_url
        }
        results.append('\n'.join(f'{k}: {v}' for k, v in paper_info.items()))
    
    return '\n\n'.join(results) if results else "No papers found matching the criteria."

# Create the function tool
arxiv_search_tool = FunctionTool(
    name="arxiv_search",
    description="Search arXiv for academic papers based on keywords and categories. Returns paper titles, summaries, and links.",
    params_json_schema={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "The search query to find relevant papers"
            },
            "max_results": {
                "type": "integer",
                "description": "Maximum number of results to return (default: 5)",
                "minValue": 1,
                "maxValue": 100
            },
            "categories": {
                "type": "array",
                "items": {
                    "type": "string"
                },
                "description": "List of arXiv categories to filter by (e.g. 'cs.AI' for Artificial Intelligence, 'quant-ph' for Quantum Physics)"
            }
        },
        "required": ["query", "max_results", "categories"],
        "additionalProperties": False
    },
    on_invoke_tool=arxiv_search
)

# Create the search agent
search_agent = Agent(
    name="ArXiv Search Agent",
    instructions=(
        "You are an expert at searching academic papers on arXiv. "
        "When given a research topic or question, you use the arxiv_search tool to find relevant papers. "
        "You format your responses clearly and highlight key findings."
    ),
    tools=[arxiv_search_tool]
)
