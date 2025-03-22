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

def generate_search_combinations(keywords: List[str], context: Dict[str, Any]) -> List[str]:
    """Generate boolean search combinations from keywords."""
    # Create a single, less restrictive search query
    combinations = []
    
    # Extract constraints from context
    min_year = context.get('min_year', 2020)
    max_year = context.get('max_year', 2025)
    year_constraint = f"year:[{min_year} TO {max_year}]"
    
    # If we have keywords, use them to create additional combinations
    if keywords and len(keywords) >= 3:
        # Group keywords in meaningful combinations
        for i in range(0, len(keywords), 3):
            if i + 2 < len(keywords):
                term1, term2, term3 = keywords[i], keywords[i+1], keywords[i+2]
                combinations.append(f"({term1} OR {term2}) AND {term3} ")
            elif len(keywords) == 2:
                combinations.append(f"({keywords[0]} OR {keywords[1]})")
            else:    # If there are fewer than 3 keywords, use the last one as a combination
                combinations.append(f"{keywords[-1]}")
    
    return combinations

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
               - Core concepts (transformers, NLP, performance)
               - Related concepts (efficiency, optimization)
               - Technical terms (architecture, methodology)
               - Variations and synonyms
            3. Focus on both specific and broad terms
            4. Consider recent developments and trends
            
            You must output your response in the following JSON format:
            {
                "keywords": [
                    "term1",
                    "term2",
                    ...
                ],
                "constraints": {
                    "field": "value",
                    "categories": ["category1", "category2"],
                    ...
                }
            }"""
            
            # Create the user message with the research question and context
            user_message = f"""Please analyze this research question and generate a comprehensive search strategy:
            Research Question: {research_question}
            Context: {json.dumps(context) if context else '{}'}
            
            Focus on:
            1. Core concepts in transformer architectures and NLP
            2. Performance and efficiency terms
            3. Technical and methodological terms
            4. Recent developments and innovations"""
            
            # Call the OpenAI API with a timeout
            try:
                response = await asyncio.wait_for(
                    asyncio.to_thread(
                        self.client.chat.completions.create,
                        model="gpt-4-turbo-preview",
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
                keywords = response_data.get("keywords", [])
                
                # Generate search combinations
                combinations = generate_search_combinations(keywords, context or {})
                
                # Create the output
                return SearchStrategy(
                    keywords=keywords,
                    combinations=combinations,
                    constraints=context or {}
                )
                
            except (json.JSONDecodeError, KeyError) as e:
                raise ValueError(f"Invalid response format: {str(e)}")
            
        except TimeoutError:
            raise  # Re-raise TimeoutError without wrapping
        except Exception as e:
            raise RuntimeError(f"Failed to analyze keywords: {str(e)}") from e

async def analyze_keywords(_, args_json: str) -> str:
    """Analyze research question to generate search keywords."""
    args = KeywordAnalysisInput.model_validate_json(args_json)
    
    try:
        # Create the system message with instructions
        system_message = """You are an expert at analyzing research questions to identify effective search keywords.
        Your task is to:
        1. Extract key concepts and terms
        2. Identify synonyms and related terms
        3. Consider variations in terminology
        4. Include both specific and broader terms
        5. Consider domain-specific vocabulary
        
        You must output your response in the following JSON format:
        {
            "keywords": ["keyword1", "keyword2", ...],
            "combinations": ["combination1", "combination2", ...],
            "constraints": {
                "constraint1": "value1",
                ...
            }
        }"""
        
        # Create the user message with the research question and context
        user_message = f"""Please analyze this research question and context to generate search keywords:
        
        Research Question: {args.research_question.question}
        Context: {json.dumps(args.context)}
        
        Focus on:
        1. Core concepts in transformer architectures and NLP
        2. Performance and efficiency terms
        3. Technical and methodological terms
        4. Recent developments and innovations"""
        
        # Call the OpenAI API with a timeout
        try:
            response = await asyncio.wait_for(
                asyncio.to_thread(
                    client.chat.completions.create,
                    model="gpt-4-turbo-preview",
                    response_format={"type": "json_object"},
                    messages=[
                        {"role": "system", "content": system_message},
                        {"role": "user", "content": user_message}
                    ]
                ),
                timeout=timeout
            )
        except asyncio.TimeoutError:
            raise TimeoutError("Assistant took too long to respond")
        
        # Parse the response
        try:
            response_data = json.loads(response.choices[0].message.content)
            keywords = response_data.get("keywords", [])
            
            # Generate search combinations
            combinations = generate_search_combinations(keywords, args.context)
            
            # Create the output
            output = SearchStrategy(
                keywords=keywords,
                combinations=combinations,
                constraints=args.context
            )
            
            return output.model_dump_json()
            
        except (json.JSONDecodeError, KeyError) as e:
            raise ValueError(f"Invalid response format: {str(e)}")
        
    except TimeoutError:
        raise  # Re-raise TimeoutError without wrapping
    except Exception as e:
        raise RuntimeError(f"Failed to analyze keywords: {str(e)}") from e 