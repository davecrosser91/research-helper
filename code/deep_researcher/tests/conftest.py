import os
import time
import asyncio
import pytest
from openai import OpenAI

@pytest.fixture
def mock_openai_client(monkeypatch):
    """Mock OpenAI client for testing."""
    class MockResponse:
        def __init__(self, content):
            self.content = content
            
        @property
        def choices(self):
            return [type('Choice', (), {'message': type('Message', (), {'content': self.content})()})]
    
    class MockOpenAI:
        def __init__(self):
            self.chat = type('Chat', (), {
                'completions': type('Completions', (), {
                    'create': self.mock_create
                })
            })
        
        def mock_create(self, **kwargs):
            # Simulate a delay to test timeout
            time.sleep(2)  # Sleep for 2 seconds
            return MockResponse('''{
                "primary_keywords": ["test keyword 1", "test keyword 2"],
                "secondary_keywords": ["secondary 1", "secondary 2"],
                "technical_terms": ["term 1", "term 2"],
                "explanations": {
                    "term 1": "explanation 1",
                    "term 2": "explanation 2"
                },
                "related_concepts": ["concept 1", "concept 2"]
            }''')
    
    monkeypatch.setattr("openai.OpenAI", MockOpenAI)
    return MockOpenAI()

@pytest.fixture
def real_openai_client():
    """Real OpenAI client for integration tests."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set")
    return OpenAI() 