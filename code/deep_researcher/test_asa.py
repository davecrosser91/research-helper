import asyncio
from openai import OpenAI
from deep_researcher.research_agents.abstract_screening_agent import AbstractScreeningAgent

async def main():
    # Create an instance of the Abstract Screening Agent with OpenAI client
    client = OpenAI()  # Make sure you have OPENAI_API_KEY in your environment
    agent = AbstractScreeningAgent(client=client)
    
    # Test papers
    papers = [
        {
            "paper_id": "2103.12345",
            "title": "Efficient Transformer Architectures for NLP Tasks",
            "authors": ["John Doe", "Jane Smith"],
            "abstract": """
            This paper presents novel modifications to transformer architectures that significantly improve 
            their performance on various NLP tasks. We introduce a new attention mechanism that reduces 
            computational complexity while maintaining accuracy. Experimental results show 30% faster 
            training and inference times with comparable or better results on standard benchmarks.
            """,
            "metadata": {"year": 2023, "citations": 45}
        },
        {
            "paper_id": "2104.67890",
            "title": "Survey of Transformer Models in NLP",
            "authors": ["Alice Johnson", "Bob Wilson"],
            "abstract": """
            We provide a comprehensive survey of transformer architectures in natural language processing.
            The paper covers recent developments, optimization techniques, and applications across different
            domains. We analyze performance trends and identify promising future research directions.
            """,
            "metadata": {"year": 2023, "citations": 120}
        }
    ]
    
    # Screening criteria
    criteria = {
        "relevance_criteria": {
            "focuses_on_transformer_architectures": True,
            "addresses_performance_optimization": True,
            "includes_empirical_results": True
        },
        "quality_criteria": {
            "clear_methodology": True,
            "reproducible_results": True,
            "sufficient_evaluation": True
        },
        "recency": {
            "min_year": 2020
        }
    }
    
    # Research context
    context = {
        "research_question": "How do modifications in transformer architecture designs affect performance optimization and application outcomes in current natural language processing tasks?",
        "focus_areas": ["architecture design", "performance optimization", "applications"]
    }
    
    # Screen papers
    try:
        results = await agent.screen_papers(papers, criteria, context)
        
        # Print results for each paper
        for paper in results:
            print(f"\n=== Screening Results for: {paper.title} ===")
            print(f"Relevance Score: {paper.relevance_score}")
            print("\nInclusion Criteria:")
            for criterion, met in paper.inclusion_criteria.items():
                print(f"- {criterion}: {'✓' if met else '✗'}")
            print(f"\nPriority Rank: {paper.priority_rank}")
            print(f"\nRationale: {paper.metadata.get('rationale', 'No rationale provided')}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 