import pytest
from research_agents.search_agent import arxiv_search, ArxivSearchArgs, search_agent
from agents import Runner
import json
from pydantic import ValidationError

@pytest.mark.asyncio
async def test_arxiv_search_direct():
    """Test the arxiv_search function directly."""
    # Test data
    args = ArxivSearchArgs(
        query="quantum computing",
        max_results=2,
        categories=["cs.AI"]
    )
    
    # Convert to JSON as the function expects
    args_json = args.model_dump_json()
    
    # Call the search function
    result = await arxiv_search(None, args_json)
    
    # Verify the result
    assert isinstance(result, str)
    assert "Title:" in result
    assert "Authors:" in result
    assert "Summary:" in result
    assert "ArXiv ID:" in result

@pytest.mark.asyncio
async def test_search_agent():
    """Test the complete search agent with a simple query."""
    result = await Runner.run(
        search_agent,
        "Search for papers about quantum computing in the AI field",
    )
    
    # Verify the agent's response
    assert result.final_output is not None
    assert isinstance(result.final_output, str)
    assert len(result.final_output) > 0

@pytest.mark.asyncio
async def test_search_agent_with_categories():
    """Test the search agent with specific categories."""
    query = (
        "Find papers about quantum computing in the quantum physics "
        "and artificial intelligence categories (cs.AI and quant-ph)"
    )
    
    result = await Runner.run(
        search_agent,
        query,
    )
    
    # Verify the response
    assert result.final_output is not None
    assert isinstance(result.final_output, str)
    assert len(result.final_output) > 0

@pytest.mark.asyncio
async def test_invalid_search():
    """Test the search with invalid parameters."""
    with pytest.raises(ValidationError):
        invalid_args = ArxivSearchArgs(
            query="",  # Empty query should fail
            max_results=-1,  # Invalid number
            categories=["invalid-category"]  # Invalid category
        )

def test_arxiv_search_args_validation():
    """Test ArxivSearchArgs validation."""
    # Valid args
    args = ArxivSearchArgs(
        query="quantum computing",
        max_results=5,
        categories=["cs.AI"]
    )
    assert args.query == "quantum computing"
    assert args.max_results == 5
    assert args.categories == ["cs.AI"]
    
    # Test empty query
    with pytest.raises(ValidationError):
        ArxivSearchArgs(
            query="   ",  # Empty or whitespace query
            max_results=5,
            categories=["cs.AI"]
        )
    
    # Test invalid max_results
    with pytest.raises(ValidationError):
        ArxivSearchArgs(
            query="quantum",
            max_results=-1,  # Negative number
            categories=["cs.AI"]
        )
    
    # Test invalid categories
    with pytest.raises(ValidationError):
        ArxivSearchArgs(
            query="quantum",
            max_results=5,
            categories=["invalid-category"]
        ) 