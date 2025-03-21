import os
import pytest
from dotenv import load_dotenv

def pytest_configure(config):
    """Set up test environment before running tests."""
    # Load environment variables from .env file
    load_dotenv()
    
    # Ensure OPENAI_API_KEY is set
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY environment variable is not set")

@pytest.fixture(scope="session")
def sample_arxiv_categories():
    """Provide a list of valid ArXiv categories for testing."""
    return [
        "cs.AI",     # Artificial Intelligence
        "quant-ph",  # Quantum Physics
        "cs.LG",     # Machine Learning
        "cs.CL",     # Computation and Language
        "cs.NE",     # Neural and Evolutionary Computing
        "stat.ML",   # Machine Learning (Statistics)
        "cs.CV",     # Computer Vision
        "cs.RO",     # Robotics
        "cs.HC"      # Human-Computer Interaction
    ] 