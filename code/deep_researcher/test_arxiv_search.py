import asyncio
import arxiv
import json
from datetime import datetime
from typing import List, Dict, Any

async def test_arxiv_search():
    print("Starting ArXiv Search Test")
    
    # Test different query formats
    queries = [
        # Test 1: Simple query
        "(transformer OR transformers) AND (nlp OR 'natural language processing')",
        
        # Test 2: Query with explicit field tags
        'ti:"transformer" AND (cat:cs.CL OR cat:cs.AI)',
        
        # Test 3: Query with date range using proper ArXiv syntax
        'ti:"transformer" AND submittedDate:[20200101 TO 20240231]',
        
        # Test 4: Most basic query possible
        "transformer"
    ]
    
    client = arxiv.Client()
    
    for i, query in enumerate(queries, 1):
        print(f"\nTest {i}: Trying query: {query}")
        try:
            search = arxiv.Search(
                query=query,
                max_results=5,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )
            
            results = []
            search_iter = client.results(search)
            
            for result in search_iter:
                paper = {
                    "arxiv_id": result.entry_id.split('/')[-1],
                    "title": result.title,
                    "authors": [author.name for author in result.authors],
                    "abstract": result.summary[:200] + "...",  # Truncate for readability
                    "categories": result.categories,
                    "published_date": result.published.isoformat()
                }
                results.append(paper)
                print(f"\nFound paper: {paper['title']}")
                print(f"Categories: {', '.join(paper['categories'])}")
                print(f"Published: {paper['published_date']}")
            
            print(f"\nTotal results for query {i}: {len(results)}")
            
        except Exception as e:
            print(f"Error with query {i}: {str(e)}")

async def main():
    try:
        await test_arxiv_search()
    except Exception as e:
        print(f"\nTest failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 