import pytest
from research_agents.writer_agent import writer_agent
from agents import Runner

@pytest.mark.asyncio
async def test_writer_agent():
    """Test the writer agent with a simple writing task."""
    result = await Runner.run(
        writer_agent,
        "Write a brief summary of quantum computing basics",
    )
    
    # Verify the agent's response
    assert result.final_output is not None
    assert isinstance(result.final_output, str)
    assert len(result.final_output) > 0
    
    # Check for writing quality
    output = result.final_output.lower()
    assert "quantum" in output
    assert len(output.split()) >= 50  # Ensure minimum length
    assert any(word in output for word in ["is", "are", "the", "this"])  # Basic grammar check

@pytest.mark.asyncio
async def test_writer_agent_technical():
    """Test the writer agent with a technical writing task."""
    result = await Runner.run(
        writer_agent,
        "Write a technical explanation of quantum entanglement and its role in quantum computing",
    )
    
    # Verify the response
    assert result.final_output is not None
    assert isinstance(result.final_output, str)
    assert len(result.final_output) > 0
    
    # Check for technical content
    output = result.final_output.lower()
    assert all(term in output for term in ["entanglement", "quantum", "state"])
    assert len(output.split()) >= 100  # Ensure comprehensive explanation 