import pytest
from deep_researcher.research_agents.keyword_agent import KeywordAgent, KeywordAnalysisInput

@pytest.mark.asyncio
async def test_keyword_analysis_basic(mock_openai_client):
    """Test basic keyword analysis functionality."""
    agent = KeywordAgent(client=mock_openai_client)
    input_data = KeywordAnalysisInput(
        research_topic="Impact of artificial intelligence on healthcare diagnostics",
        field_context="Medical Technology",
        focus_areas=["machine learning", "diagnostic accuracy"]
    )
    
    result = await agent.analyze_keywords(input_data)
    
    # Check that all required fields are present
    assert result.primary_keywords
    assert result.secondary_keywords
    assert result.technical_terms
    assert result.explanations
    assert result.related_concepts
    
    # Check that we have the expected mock data
    assert "test keyword 1" in result.primary_keywords
    assert "secondary 1" in result.secondary_keywords
    assert "term 1" in result.technical_terms
    assert result.explanations["term 1"] == "explanation 1"
    assert "concept 1" in result.related_concepts

@pytest.mark.asyncio
async def test_keyword_analysis_minimal_input(mock_openai_client):
    """Test keyword analysis with minimal input."""
    agent = KeywordAgent(client=mock_openai_client)
    input_data = KeywordAnalysisInput(
        research_topic="quantum computing basics",
    )
    
    result = await agent.analyze_keywords(input_data)
    
    # Check that all required fields are present even with minimal input
    assert result.primary_keywords
    assert result.secondary_keywords
    assert result.technical_terms
    assert result.explanations
    assert result.related_concepts
    
    # Check that we have the expected mock data
    assert "test keyword 1" in result.primary_keywords

@pytest.mark.asyncio
async def test_keyword_analysis_timeout(mock_openai_client):
    """Test that the agent properly handles timeouts."""
    agent = KeywordAgent(client=mock_openai_client, timeout=1)  # Set a very short timeout
    input_data = KeywordAnalysisInput(
        research_topic="Complex analysis of multidimensional quantum field theories",
        field_context="Theoretical Physics",
        focus_areas=["quantum mechanics", "field theory"]
    )
    
    with pytest.raises(TimeoutError):
        await agent.analyze_keywords(input_data)

@pytest.mark.asyncio
@pytest.mark.integration
async def test_keyword_analysis_integration(real_openai_client):
    """Integration test with real OpenAI API."""
    agent = KeywordAgent(client=real_openai_client)
    input_data = KeywordAnalysisInput(
        research_topic="machine learning in climate change prediction",
        field_context="Environmental Science",
        focus_areas=["predictive modeling", "climate data"]
    )
    
    result = await agent.analyze_keywords(input_data)
    
    # Check that all required fields are present
    assert result.primary_keywords
    assert result.secondary_keywords
    assert result.technical_terms
    assert result.explanations
    assert result.related_concepts
    
    # Check that we have relevant keywords
    assert any("machine learning" in kw.lower() or "ml" in kw.lower() 
              for kw in result.primary_keywords)
    assert any("climate" in kw.lower() 
              for kw in result.primary_keywords + result.secondary_keywords) 