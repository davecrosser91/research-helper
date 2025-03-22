import pytest
import pytest_asyncio
import os
from deep_researcher.research_agents.research_question_agent import ResearchQuestionAgent
from deep_researcher.research_agents.types import FormulateQuestionInput

@pytest_asyncio.fixture
async def research_question_agent():
    """Create a research question agent for testing."""
    return ResearchQuestionAgent(timeout=180)  # 3 minute timeout for tests

@pytest.mark.asyncio
async def test_research_question_formulation(research_question_agent):
    """Test that the agent can formulate a valid research question."""
    input_data = FormulateQuestionInput(
        research_area="quantum computing applications in cryptography",
        constraints={
            "time_frame": "2020-2024",
            "focus_areas": ["post-quantum cryptography", "quantum key distribution"],
            "scope": "academic research papers and industry implementations"
        }
    )
    
    result = await research_question_agent.formulate_question(input_data)
    
    # Verify the structure of the response
    assert result.question.question is not None
    assert isinstance(result.question.sub_questions, list)
    assert isinstance(result.question.scope, dict)
    assert isinstance(result.validation, dict)
    
    # Verify FINER criteria validation
    assert all(key in result.validation for key in ["feasible", "interesting", "novel", "ethical", "relevant"])
    assert all(isinstance(value, bool) for value in result.validation.values())
    
    # Verify question content
    question = result.question.question.lower()
    assert "quantum" in question
    assert "cryptography" in question
    assert "?" in question

@pytest.mark.asyncio
async def test_research_question_edge_cases(research_question_agent):
    """Test the agent with minimal input and detailed constraints."""
    # Test with minimal input
    minimal_input = FormulateQuestionInput(
        research_area="machine learning in healthcare",
        constraints={}
    )
    
    minimal_result = await research_question_agent.formulate_question(minimal_input)
    assert minimal_result.question.question is not None
    assert "?" in minimal_result.question.question
    
    # Test with detailed constraints
    detailed_input = FormulateQuestionInput(
        research_area="machine learning in healthcare",
        constraints={
            "time_frame": "2022-2024",
            "focus_areas": ["diagnostic imaging", "predictive analytics"],
            "scope": "clinical applications only",
            "population": "adult patients",
            "methodology": "retrospective studies",
            "data_requirements": "anonymized medical records",
            "ethical_considerations": ["patient privacy", "bias mitigation"]
        }
    )
    
    detailed_result = await research_question_agent.formulate_question(detailed_input)
    assert detailed_result.question.question is not None
    assert len(detailed_result.question.sub_questions) > 0  # Should generate sub-questions for detailed input
    assert "methodology" in detailed_result.question.scope  # Should include methodology in scope
    
    # Verify question content
    question = detailed_result.question.question.lower()
    assert "machine learning" in question or "ml" in question
    # The question might use terms like "clinical", "medical", "patient care" instead of "healthcare"
    assert any(term in question for term in ["healthcare", "health", "clinical", "medical", "patient"])

@pytest.mark.asyncio
async def test_research_question_timeout(research_question_agent):
    """Test that the agent properly handles timeouts."""
    # Create an agent with a very short timeout
    agent = ResearchQuestionAgent(timeout=1)
    
    input_data = FormulateQuestionInput(
        research_area="quantum computing applications in cryptography",
        constraints={"scope": "theoretical studies"}
    )
    
    with pytest.raises(TimeoutError):
        await agent.formulate_question(input_data)