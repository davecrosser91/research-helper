from typing import Dict, List, Optional
import asyncio
import json
from openai import OpenAI
from pydantic import BaseModel, Field

class KeywordAnalysis(BaseModel):
    """Model for keyword analysis output."""
    primary_keywords: List[str] = Field(..., description="Main keywords that directly relate to the core topic")
    secondary_keywords: List[str] = Field(..., description="Supporting or related keywords")
    technical_terms: List[str] = Field(..., description="Specialized technical terms in the field")
    explanations: Dict[str, str] = Field(..., description="Brief explanations for important terms")
    related_concepts: List[str] = Field(..., description="Related research concepts or areas")

class KeywordAnalysisInput(BaseModel):
    """Model for keyword analysis input."""
    research_topic: str = Field(..., description="The research topic or question to analyze")
    field_context: Optional[str] = Field(None, description="Additional context about the research field")
    focus_areas: Optional[List[str]] = Field(None, description="Specific areas to focus on")

class KeywordAgent:
    """Agent for analyzing keywords in research topics."""
    
    def __init__(self, client: OpenAI = None, timeout: int = 60):
        self.client = client or OpenAI()
        self.timeout = timeout
        
    async def analyze_keywords(self, input_data: KeywordAnalysisInput) -> KeywordAnalysis:
        """Analyze keywords from a research topic."""
        try:
            # Create the system message with instructions
            system_message = """You are an expert at analyzing research topics and extracting relevant keywords.
            Your task is to:
            1. Identify primary keywords that are central to the topic
            2. Find secondary keywords that support or relate to the main concepts
            3. Extract technical terms specific to the field
            4. Provide brief, clear explanations for important terms
            5. Suggest related research concepts or areas
            
            Format your response as a JSON object with the following structure:
            {
                "primary_keywords": ["keyword1", "keyword2"],
                "secondary_keywords": ["keyword1", "keyword2"],
                "technical_terms": ["term1", "term2"],
                "explanations": {
                    "term1": "brief explanation",
                    "term2": "brief explanation"
                },
                "related_concepts": ["concept1", "concept2"]
            }"""
            
            # Create the user message with the research topic and context
            user_message = f"""Please analyze the following research topic:
            Topic: {input_data.research_topic}
            Field Context: {input_data.field_context or 'Not specified'}
            Focus Areas: {', '.join(input_data.focus_areas) if input_data.focus_areas else 'Not specified'}
            
            Please provide a comprehensive keyword analysis following the specified format."""
            
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
                raise TimeoutError("Analysis took too long to complete")
            
            # Parse the response
            try:
                response_data = json.loads(response.choices[0].message.content)
                return KeywordAnalysis(**response_data)
            except (json.JSONDecodeError, KeyError) as e:
                raise ValueError(f"Invalid response format: {str(e)}")
            
        except TimeoutError:
            raise
        except Exception as e:
            raise RuntimeError(f"Failed to analyze keywords: {str(e)}") from e 