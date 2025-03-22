from typing import Dict, Any, List
import asyncio
import json
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from .types import SearchStrategy

class KeywordSet(BaseModel):
    """Structure for keyword analysis results."""
    primary_terms: List[str] = Field(description="Core concept terms")
    secondary_terms: List[str] = Field(description="Related concept terms")
    synonyms: Dict[str, List[str]] = Field(description="Synonyms for primary terms")
    boolean_combinations: List[str] = Field(description="Boolean search combinations")
    constraints: Dict[str, Any] = Field(description="Search constraints")

class KeywordAnalysisAgent:
    """Agent for analyzing research questions and generating comprehensive search strategies."""
    
    def __init__(self, client: OpenAI = None, timeout: int = 120):
        self.client = client or OpenAI()
        self.timeout = timeout
        
    async def analyze(self, research_question: str, context: Dict[str, Any] = None) -> SearchStrategy:
        """Generate a comprehensive search strategy from research questions."""
        try:
            # Create the system message with instructions
            system_message = """You are an expert at keyword analysis and search strategy formulation. Your role is to:
            1. Analyze research questions to identify key concepts
            2. Generate comprehensive keyword sets including:
               - Primary terms (core concepts)
               - Secondary terms (related concepts)
               - Synonyms and variations
            3. Create effective boolean search combinations
            4. Define appropriate search constraints
            
            You must output your response in the following JSON format:
            {
                "primary_terms": ["term1", "term2"],
                "secondary_terms": ["term1", "term2"],
                "synonyms": {
                    "term1": ["synonym1", "synonym2"],
                    "term2": ["synonym1", "synonym2"]
                },
                "boolean_combinations": [
                    "combination1",
                    "combination2"
                ],
                "constraints": {
                    "date_range": "value",
                    "categories": ["category1", "category2"],
                    "max_results": number
                }
            }"""
            
            # Create the user message with the research question and context
            user_message = f"""Please analyze this research question and generate a comprehensive search strategy:
            Research Question: {research_question}
            Context: {json.dumps(context) if context else '{}'}
            
            Focus on creating precise yet comprehensive search terms that will capture relevant literature."""
            
            # Call the OpenAI API with a timeout
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat.completions.create,
                        model="gpt-4o-mini",
                        response_format={"type": "json_object"},
                        messages=[
                            {"role": "system", "content": system_message},
                            {"role": "user", "content": user_message}
                        ]
                    ),
                    timeout=self.timeout
                )
            except asyncio.TimeoutError:
                raise TimeoutError("Assistant took too long to respond")
            
            # Parse the response
            try:
                response_data = json.loads(response.choices[0].message.content)
                keyword_set = KeywordSet(**response_data)
                
                # Convert to SearchStrategy format
                keywords = (
                    keyword_set.primary_terms +
                    keyword_set.secondary_terms +
                    [syn for syns in keyword_set.synonyms.values() for syn in syns]
                )
                
                return SearchStrategy(
                    keywords=keywords,
                    combinations=keyword_set.boolean_combinations,
                    constraints=keyword_set.constraints
                )
                
            except (json.JSONDecodeError, KeyError) as e:
                raise ValueError(f"Invalid response format: {str(e)}")
            
        except TimeoutError:
            raise  # Re-raise TimeoutError without wrapping
        except Exception as e:
            raise RuntimeError(f"Failed to analyze keywords: {str(e)}") from e 