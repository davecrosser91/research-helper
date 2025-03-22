from typing import Dict, Any, Optional
import asyncio
import logging
from datetime import datetime
from openai import OpenAI

from .types import WorkflowState, FormulateQuestionInput, KeywordAnalysisInput
from .research_question_agent import ResearchQuestionAgent
from .keyword_analysis_agent import KeywordAnalysisAgent

class SystematicReviewWorkflow:
    """Manages the systematic review workflow."""
    
    def __init__(self, openai_client: OpenAI = None):
        self.logger = logging.getLogger("systematic_review")
        self.state = WorkflowState.INITIALIZING
        self.metadata: Dict[str, Any] = {}
        
        # Initialize OpenAI client
        self.client = openai_client or OpenAI()
        
        # Initialize agents
        self.research_question_agent = ResearchQuestionAgent(client=self.client)
        self.keyword_analysis_agent = KeywordAnalysisAgent(client=self.client)
        
    async def start_review(
        self,
        research_area: str,
        constraints: Dict[str, Any]
    ):
        """Start a new systematic review."""
        try:
            self.logger.info(f"Starting systematic review for: {research_area}")
            
            # Step 1: Formulate research question
            self.state = WorkflowState.QUESTION_FORMULATION
            question_input = FormulateQuestionInput(
                research_area=research_area,
                constraints=constraints
            )
            question_result = await self.research_question_agent.formulate_question(question_input)
            self.logger.info("Research question formulated")
            
            # Step 2: Keyword analysis
            self.state = WorkflowState.KEYWORD_ANALYSIS
            keyword_result = await self.keyword_analysis_agent.analyze(
                question_result.question.question,
                context={
                    "field": research_area,
                    "sub_questions": question_result.question.sub_questions,
                    "constraints": constraints
                }
            )
            self.logger.info("Keyword analysis completed")
            
            # Return combined results
            return {
                "research_question": question_result,
                "search_strategy": keyword_result
            }
            
        except Exception as e:
            self.state = WorkflowState.ERROR
            self.logger.error(f"Workflow error: {str(e)}")
            raise

# Example usage:
"""
async def main():
    workflow = SystematicReviewWorkflow()
    result = await workflow.start_review(
        research_area="transformer architectures in natural language processing",
        constraints={
            "time_frame": "current",
            "focus_areas": ["architecture design", "performance optimization", "applications"],
            "scope": "theoretical and empirical studies"
        }
    )
    print(result)

if __name__ == "__main__":
    asyncio.run(main())
""" 