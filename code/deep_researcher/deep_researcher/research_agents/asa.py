from typing import List, Dict, Any
from ..models.base import PaperResult

class AbstractScreeningAgent:
    """Agent for screening and ranking paper abstracts"""
    
    def __init__(self):
        self.system_prompt = """You are an Abstract Screening Specialist. Your role is to:
1. Analyze paper abstracts for relevance to the research question
2. Score papers based on:
   - Methodology match
   - Topic alignment
   - Time relevance
   - Citation impact
3. Rank papers by priority
4. Identify key themes and patterns
"""

    async def screen(self, papers: List[PaperResult]) -> List[PaperResult]:
        """Screen and rank papers based on relevance"""
        # For now, return mock relevance scores
        # TODO: Integrate with actual LLM for intelligent scoring
        
        for i, paper in enumerate(papers):
            # Mock scoring based on simple heuristics
            score = 0.0
            
            # Check title for relevant keywords
            if "survey" in paper.title.lower() or "review" in paper.title.lower():
                score += 0.3
            
            # Check if paper is from a relevant category
            if any(cat.startswith("cs.") for cat in paper.metadata.get("categories", [])):
                score += 0.2
                
            # Add some randomness for demo
            import random
            score += random.uniform(0, 0.5)
            
            # Ensure score is between 0 and 1
            paper.relevance_score = min(1.0, max(0.0, score))
            
        # Sort papers by score
        return sorted(papers, key=lambda p: p.relevance_score or 0, reverse=True) 