import asyncio
import json
from deep_researcher.research_agents.search_execution_agent import search_execution_tool

async def test_search():
    print("Testing ArXiv Search...")
    
    # Test search with simple query
    search_args = {
        "query": "(transformer OR transformers) AND (nlp OR 'natural language processing')",
        "max_results": 5,
        "batch_size": 5,
        "categories": ["cs.CL", "cs.AI", "cs.LG"],
        "min_date": "2020-01-01",
        "max_date": "2024-12-31"
    }
    
    try:
        print(f"\nExecuting search with query: {search_args['query']}")
        results = await search_execution_tool.on_invoke_tool(None, json.dumps(search_args))
        batches = json.loads(results)
        
        # Print results
        for batch in batches:
            print(f"\nBatch {batch['batch_number']}:")
            print(f"Total processed: {batch['total_processed']}")
            print(f"Has more: {batch['has_more']}")
            
            print("\nPapers:")
            for paper in batch['papers']:
                print(f"\nTitle: {paper['title']}")
                print(f"Authors: {', '.join(paper['authors'])}")
                print(f"Categories: {', '.join(paper['categories'])}")
                print(f"Published: {paper['published_date']}")
                print(f"ArXiv ID: {paper['arxiv_id']}")
                print(f"Abstract: {paper['abstract'][:200]}...")
        
        return batches
        
    except Exception as e:
        print(f"\nError during search: {str(e)}")
        raise

async def main():
    try:
        await test_search()
    except Exception as e:
        print(f"\nTest failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 