import asyncio
import json
from datetime import datetime
from search_execution_agent import search_execution
from abstract_screening_agent import screen_abstracts, MethodologyType, RelevanceScore

async def test_screening():
    # First, get some papers using the search execution agent
    search_query = {
        "query": "quantum machine learning applications",
        "max_results": 10,
        "categories": ["quant-ph", "cs.AI"],
        "batch_size": 5,
        "min_date": "2024-01-01"
    }
    
    try:
        print("Step 1: Executing search...")
        search_results = await search_execution(None, json.dumps(search_query))
        search_data = json.loads(search_results)
        
        # Extract papers from search results
        papers = []
        for batch in search_data:
            papers.extend(batch['papers'])
        
        print(f"\nFound {len(papers)} papers to screen")
        
        # Define screening criteria
        screening_query = {
            "papers": papers,
            "criteria": {
                "required_keywords": ["quantum", "machine learning", "application"],
                "excluded_keywords": ["classical", "traditional"],
                "methodology_types": [
                    MethodologyType.EXPERIMENTAL.value,
                    MethodologyType.THEORETICAL.value
                ],
                "min_relevance_score": RelevanceScore.LOW.value,
                "custom_criteria": {
                    "prefer_recent": True
                }
            },
            "batch_size": 5,
            "min_confidence": 0.7
        }
        
        print("\nStep 2: Screening papers...")
        screening_results = await screen_abstracts(None, json.dumps(screening_query))
        screening_data = json.loads(screening_results)
        
        print("\nScreening Results:")
        for batch in screening_data:
            print(f"\nBatch {batch['batch_id']}:")
            print(f"Statistics: {json.dumps(batch['batch_statistics'], indent=2)}")
            
            print("\nTop Themes:")
            for theme in batch['batch_themes'][:3]:  # Show top 3 themes
                print(f"- {theme['theme_name']} (frequency: {theme['frequency']})")
            
            print("\nPapers by Priority:")
            for paper in sorted(batch['papers'], key=lambda x: x['priority_rank']):
                print(f"\nRank {paper['priority_rank']}:")
                print(f"Title: {paper['title']}")
                print(f"Relevance: {paper['relevance_score']}")
                print(f"Methodology: {paper['methodology_type']}")
                print(f"Detailed Review: {'Yes' if paper['detailed_review_flag'] else 'No'}")
                print("-" * 80)
        
        print("\nScreening completed successfully!")
        
    except Exception as e:
        print(f"Error during screening: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_screening()) 