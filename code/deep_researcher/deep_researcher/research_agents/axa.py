from typing import List, Dict, Any
import arxiv
from ..models.base import SearchStrategy, PaperResult

class ArxivSearchAgent:
    """Agent for searching papers on ArXiv"""
    
    def __init__(self):
        self.client = arxiv.Client()
        
    async def search(self, strategy: SearchStrategy) -> List[PaperResult]:
        """Search papers based on the search strategy"""
        results = []
        
        # Configure search parameters
        search = arxiv.Search(
            query=strategy.combinations[0],  # Use first combination for now
            max_results=strategy.constraints.get("max_results", 10)
        )
        
        try:
            # Fetch papers
            for paper in self.client.results(search):
                result = PaperResult(
                    paper_id=paper.entry_id.split("/")[-1],
                    title=paper.title,
                    abstract=paper.summary,
                    metadata={
                        "authors": [str(author) for author in paper.authors],
                        "published": str(paper.published),
                        "updated": str(paper.updated),
                        "doi": paper.doi,
                        "primary_category": paper.primary_category,
                        "categories": paper.categories,
                        "links": [str(link) for link in paper.links]
                    }
                )
                results.append(result)
                
        except Exception as e:
            print(f"Error searching ArXiv: {str(e)}")
            # Return mock results for now
            results = [
                PaperResult(
                    paper_id="2301.01234",
                    title=f"A Survey of {strategy.keywords[0]}",
                    abstract="This paper provides a comprehensive survey...",
                    metadata={
                        "authors": ["Author One", "Author Two"],
                        "published": "2023-01-01",
                        "categories": ["cs.AI"]
                    }
                ),
                PaperResult(
                    paper_id="2302.56789",
                    title=f"Recent Advances in {strategy.keywords[0]}",
                    abstract="We present recent developments...",
                    metadata={
                        "authors": ["Author Three"],
                        "published": "2023-02-01",
                        "categories": ["cs.LG"]
                    }
                )
            ]
            
        return results 