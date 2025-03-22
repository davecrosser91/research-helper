import asyncio
import json
from search_execution_agent import search_execution

async def test_search():
    # Test case with quantum computing papers
    query = {
        "query": "quantum computing applications",
        "max_results": 10,  # Small number for testing
        "categories": ["quant-ph", "cs.AI"],
        "batch_size": 5,
        "min_date": "2024-01-01"  # Recent papers only
    }
    
    try:
        print("Starting search execution...")
        result = await search_execution(None, json.dumps(query))
        
        # Parse and pretty print the results
        papers = json.loads(result)
        print("\nSearch Results:")
        for batch in papers:
            print(f"\nBatch {batch['batch_number']}:")
            for paper in batch['papers']:
                print(f"\nTitle: {paper['title']}")
                print(f"Authors: {', '.join(paper['authors'])}")
                print(f"ArXiv ID: {paper['arxiv_id']}")
                print(f"Categories: {', '.join(paper['categories'])}")
                print("-" * 80)
        
        print("\nSearch completed successfully!")
        
    except Exception as e:
        print(f"Error during search: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_search()) 