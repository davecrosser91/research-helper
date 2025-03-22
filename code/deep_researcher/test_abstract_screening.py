import asyncio
import json
from datetime import datetime
from openai import OpenAI
from deep_researcher.research_agents.abstract_screening_agent import (
    ScreeningCriteria,
    MethodologyType,
    RelevanceScore,
    screen_abstracts,
    AbstractScreeningArgs
)

async def get_test_papers():
    """Mock papers for testing"""
    return [
        {
            "arxiv_id": "2401.00001",
            "title": "Efficient Transformer Architectures for NLP",
            "authors": ["Alice Smith", "Bob Jones"],
            "abstract": "We present experimental results on a new transformer architecture that significantly improves efficiency in natural language processing tasks. Our approach combines attention mechanisms with novel optimization techniques.",
            "categories": ["cs.CL", "cs.AI"],
            "published_date": "2024-01-01"
        },
        {
            "arxiv_id": "2401.00002",
            "title": "A Survey of Recent NLP Advances",
            "authors": ["Charlie Brown"],
            "abstract": "This review paper provides a comprehensive survey of recent developments in natural language processing, with a focus on transformer-based models and their applications.",
            "categories": ["cs.CL"],
            "published_date": "2024-01-02"
        },
        {
            "arxiv_id": "2401.00003",
            "title": "Theoretical Analysis of Self-Attention",
            "authors": ["David Wilson", "Eve Anderson"],
            "abstract": "We present a theoretical framework for analyzing self-attention mechanisms in transformer models, providing mathematical proofs for their effectiveness in capturing long-range dependencies.",
            "categories": ["cs.LG", "cs.CL"],
            "published_date": "2024-01-03"
        }
    ]

async def test_abstract_screening():
    print("Starting Abstract Screening Test")
    
    # Use the exact keywords we got from previous keyword analysis
    required_keywords = [
        "transformer architectures",
        "natural language processing",
        "NLP advancements",
        "deep learning in NLP",
        "transformer models"
    ]
    
    try:
        # Get test papers
        papers = await get_test_papers()
        print(f"\nScreening {len(papers)} papers...")
        
        # Create screening arguments
        screening_args = {
            "papers": papers,
            "criteria": {
                "required_keywords": required_keywords,
                "excluded_keywords": [],
                "methodology_types": [
                    MethodologyType.EXPERIMENTAL.value,
                    MethodologyType.THEORETICAL.value,
                    MethodologyType.REVIEW.value
                ],
                "min_relevance_score": RelevanceScore.LOW.value
            },
            "batch_size": 10,
            "min_confidence": 0.7
        }
        
        # Screen papers
        print("\nRunning abstract screening...")
        results_json = await screen_abstracts(None, json.dumps(screening_args))
        batches = json.loads(results_json)
        
        # Print results
        print("\nScreening Results:")
        for batch in batches:
            print(f"\nBatch {batch['batch_id']}:")
            print(f"Statistics: {json.dumps(batch['batch_statistics'], indent=2)}")
            
            print("\nPapers in batch:")
            for i, (paper, result) in enumerate(zip(papers, batch['papers'])):
                print(f"\nPaper {i+1}:")
                print(f"Title: {paper['title']}")
                print(f"Relevance Score: {result['relevance_score']:.2f}")
                print(f"Priority Rank: {result['priority_rank']}")
                print(f"Inclusion Criteria: {json.dumps(result['inclusion_criteria'], indent=2)}")
                print(f"Rationale: {result['rationale']}")
            
            print("\nIdentified Themes:")
            for theme in batch['batch_themes']:
                print(f"- {theme['theme_name']} (frequency: {theme['frequency']}, confidence: {theme['confidence']:.2f})")
        
        return batches
        
    except Exception as e:
        print(f"\nError during abstract screening: {str(e)}")
        raise

async def main():
    try:
        await test_abstract_screening()
    except Exception as e:
        print(f"\nTest failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 