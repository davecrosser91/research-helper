import pytest
from research_agents.planner_agent import planner_agent
from agents import Runner

@pytest.mark.asyncio
async def test_planner_agent():
    """Test the planner agent with a simple research task."""
    result = await Runner.run(
        planner_agent,
        "Plan research on quantum computing applications in AI",
    )
    
    # Verify the agent's response
    assert result.final_output is not None
    assert isinstance(result.final_output, str)
    assert len(result.final_output) > 0
    
    # Check for planning elements
    output = result.final_output.lower()
    assert any(word in output for word in ["step", "phase", "plan", "research", "investigate"])

@pytest.mark.asyncio
async def test_planner_agent_complex_task():
    """Test the planner agent with a more complex research task."""
    result = await Runner.run(
        planner_agent,
        "Plan a comprehensive research project on the intersection of quantum computing, "
        "machine learning, and cryptography, focusing on potential applications in cybersecurity",
    )
    
    # Verify the response
    assert result.final_output is not None
    assert isinstance(result.final_output, str)
    assert len(result.final_output) > 0
    
    # Check for comprehensive planning
    output = result.final_output.lower()
    assert all(topic in output for topic in ["quantum", "machine learning", "crypto"])
    assert any(word in output for word in ["timeline", "steps", "phases", "objectives"]) 