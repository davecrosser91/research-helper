import asyncio
import arxiv
import json
from datetime import datetime
from typing import List, Dict, Any

async def test_arxiv_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    print(f"Starting ArXiv search for query: {query}")
    
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.SubmittedDate
    )
    
    results = []
    try:
        search_iter = client.results(search)
        for result in search_iter:
            paper = {
                "arxiv_id": result.entry_id.split('/')[-1],
                "title": result.title,
                "authors": [author.name for author in result.authors],
                "abstract": result.summary,
                "categories": result.categories,
                "primary_category": result.primary_category,
                "published_date": result.published.isoformat(),
                "pdf_url": result.pdf_url,
                "abstract_url": result.entry_id
            }
            results.append(paper)
            print(f"Found paper: {paper['title']}")
    
    except Exception as e:
        print(f"Error during search: {str(e)}")
        raise
    
    return results

async def main():
    query = "transformer architectures in natural language processing"
    try:
        results = await test_arxiv_search(query)
        print("\nSearch Results Summary:")
        print(f"Total papers found: {len(results)}")
        print("\nDetailed Results:")
        print(json.dumps(results, indent=2))
    except Exception as e:
        print(f"Search failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 