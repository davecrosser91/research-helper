import pytest
import asyncio
import json
from datetime import datetime, timedelta
from ..deep_researcher.research_agents.workflow_orchestrator import run_workflow

@pytest.mark.asyncio
async def test_research_workflow():
    research_input = {"description": "Test description", "field": "test field"}
    result = await run_workflow(json.dumps(research_input))
    data = json.loads(result)
    assert "research_question" in data