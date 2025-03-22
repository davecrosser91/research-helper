from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
import json
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_exponential

from .search_execution_agent import search_execution_tool
from .types import SearchStrategy

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class RefinementConfig(BaseModel):
    """Configuration for keyword refinement process."""
    keywords: List[str] = Field(..., description="Keywords to analyze (can be multi-word)")
    papers_per_keyword: int = Field(default=100, description="Number of papers to retrieve per keyword")
    year_range: Optional[int] = Field(default=3, description="Year range for time constraints")

class KeywordScore(BaseModel):
    """Results for a single keyword."""
    keyword: str = Field(..., description="The keyword being analyzed")
    papers: List[Dict[str, Any]] = Field(default_factory=list, description="Found papers")
    word_count: int = Field(..., description="Number of words in keyword")
    total_hits: int = Field(..., description="Total number of keyword word hits in abstracts")
    papers_with_hits: int = Field(..., description="Number of papers containing any keyword words")
    score: float = Field(..., description="Calculated relevance score")

class RefinementResult(BaseModel):
    """Complete results of the refinement process."""
    scored_keywords: List[KeywordScore] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class KeywordRefinement:
    """Class for analyzing and scoring individual keywords based on paper content."""
    
    def __init__(self, config: RefinementConfig):
        """Initialize the refinement process with configuration."""
        self.config = config
        self.results = RefinementResult()
        
    def _calculate_score(self, total_hits: int, papers_with_hits: int, word_count: int, total_papers: int) -> float:
        """Calculate keyword score based on hits and word count.
        
        Args:
            total_hits: Total occurrences of keyword words in all abstracts
            papers_with_hits: Number of papers containing any keyword words
            word_count: Number of words in the keyword
            total_papers: Total number of papers analyzed
            
        Returns:
            float: Score weighted by word count and hit distribution
        """
        if total_papers == 0:
            return 0.0
            
        # Calculate hit rate across papers (coverage)
        coverage = papers_with_hits / total_papers
        
        # Calculate average hits per paper with hits
        intensity = total_hits / total_papers if total_papers > 0 else 0
        
        # Weight by word count (more words = higher potential relevance)
        word_weight = word_count * 0.5  # Adjust multiplier to control word count importance
        
        return (coverage + intensity) * (1 + word_weight)
        
    async def _analyze_keyword(self, keyword: str) -> KeywordScore:
        """Analyze a single keyword by searching papers and calculating hits."""
        # Prepare search query with year constraint if specified
        query = keyword
        if self.config.year_range:
            current_year = datetime.now().year
            year_constraint = f"year:[{current_year-self.config.year_range} TO {current_year}]"
            query = f"({keyword}) AND {year_constraint}"
            
        search_args = {
            "query": query,
            "max_results": self.config.papers_per_keyword,
            "batch_size": self.config.papers_per_keyword  # Set batch_size equal to max_results to get all papers in one call
        }
        
        try:
            # Execute single search
            search_results = await search_execution_tool.on_invoke_tool(None, json.dumps(search_args))
            papers = []
            if search_results:
                batches = json.loads(search_results)
                for batch in batches:
                    if isinstance(batch, dict) and 'papers' in batch:
                        papers.extend(batch['papers'])
                        
            # Calculate hits in abstracts
            keyword_words = keyword.lower().split()
            word_count = len(keyword_words)
            total_hits = 0
            papers_with_hits = 0
            
            for paper in papers:
                abstract = paper.get("abstract", "").lower()
                paper_hits = sum(abstract.count(word) for word in keyword_words)
                if paper_hits > 0:
                    papers_with_hits += 1
                total_hits += paper_hits
                
            # Calculate score
            score = self._calculate_score(total_hits, papers_with_hits, word_count, len(papers))
            
            logger.info(f"Analyzed keyword '{keyword}': found {len(papers)} papers with {total_hits} total hits")
            
            return KeywordScore(
                keyword=keyword,
                papers=papers,
                word_count=word_count,
                total_hits=total_hits,
                papers_with_hits=papers_with_hits,
                score=score
            )
            
        except Exception as e:
            logger.error(f"Analysis failed for keyword: {keyword}. Error: {str(e)}")
            return KeywordScore(
                keyword=keyword,
                papers=[],
                word_count=len(keyword.split()),
                total_hits=0,
                papers_with_hits=0,
                score=0.0
            )
            
    #@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def refine(self) -> RefinementResult:
        """
        Execute the refinement process to score keywords.
        
        Returns:
            RefinementResult containing scored keywords and metadata
        """
        print("Refining keywords...")
        start_time = datetime.now()
        self.results.metadata["start_time"] = start_time.isoformat()
        
        logger.info(f"Starting keyword refinement for {len(self.config.keywords)} keywords")
        
        # Analyze each keyword
        scored_keywords = []
        for keyword in self.config.keywords:
            logger.info(f"Processing keyword: {keyword}")
            result = await self._analyze_keyword(keyword)
            scored_keywords.append(result)
            
        # Sort by score
        scored_keywords.sort(key=lambda x: x.score, reverse=True)
        self.results.scored_keywords = scored_keywords
        
        # Finalize results
        end_time = datetime.now()
        self.results.metadata.update({
            "end_time": end_time.isoformat(),
            "duration_seconds": (end_time - start_time).total_seconds(),
            "keywords_analyzed": len(scored_keywords),
            "successful_keywords": len([k for k in scored_keywords if k.score > 0])
        })
        
        logger.info(f"Keyword refinement completed. Analyzed {len(scored_keywords)} keywords.")
        return self.results
        
    async def enhance_search_strategy(self, strategy: SearchStrategy) -> SearchStrategy:
        """
        Enhance an existing search strategy with scored keywords.
        
        Args:
            strategy: Original search strategy
            
        Returns:
            Enhanced search strategy with scored keywords
        """
        # Initialize config with strategy keywords if not already set
        if not self.config.keywords:
            self.config.keywords = strategy.keywords
            
        # Run refinement
        results = await self.refine()
        
        # Update strategy with scored keywords (sorted by relevance)
        strategy.keywords = [k.keyword for k in results.scored_keywords]
        strategy.metadata.update({
            "refinement_results": results.model_dump(),
            "refinement_timestamp": datetime.now().isoformat()
        })
        
        return strategy 