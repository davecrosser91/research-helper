from typing import Dict, Any, List
import asyncio
import json
from openai import OpenAI
from pydantic import BaseModel, Field
from dotenv import load_dotenv

load_dotenv()

from .types import (
    FormulateQuestionInput,
    FormulateQuestionOutput,
    Question,
    ResearchQuestion
)

class QuestionResponse(BaseModel):
    """Response format for research question formulation."""
    question: str = Field(description="The main research question")
    sub_questions: List[str] = Field(description="List of related sub-questions")

class ValidationResponse(BaseModel):
    """Validation response for FINER criteria."""
    feasible: bool = Field(description="Whether the question can be answered with available resources")
    interesting: bool = Field(description="Whether the question addresses a gap or need")
    novel: bool = Field(description="Whether the question adds new information")
    ethical: bool = Field(description="Whether the question considers ethical implications")
    relevant: bool = Field(description="Whether the question has practical or theoretical significance")

class AgentResponse(BaseModel):
    """Complete response from the research question agent."""
    question: QuestionResponse = Field(description="The formulated research question")
    validation: ValidationResponse = Field(description="Validation against FINER criteria")

class ResearchQuestionAgent:
    """Agent for formulating and validating research questions."""
    
    def __init__(self, client: OpenAI = None, timeout: int = 120):
        self.client = client or OpenAI()
        self.timeout = timeout
        
    async def formulate_question(self, input_data: FormulateQuestionInput) -> FormulateQuestionOutput:
        """Formulate a research question based on input parameters."""
        try:
            # Create the system message with instructions
            system_message = """You are an expert at formulating research questions following the FINER criteria:
            - Feasible: Can be answered with available resources and methods
            - Interesting: Addresses a gap or need in the field
            - Novel: Adds new information to existing knowledge
            - Ethical: Considers ethical implications
            - Relevant: Has practical or theoretical significance
            
            Your task is to help formulate clear, focused research questions that meet these criteria.
            For each question, you should:
            1. Analyze the research area and constraints
            2. Formulate a main research question
            3. Generate relevant sub-questions
            4. Define the scope
            5. Validate against FINER criteria
            
            You must output your response in the following JSON format:
            {
                "question": {
                    "question": "The main research question",
                    "sub_questions": ["Sub-question 1", "Sub-question 2"]
                },
                "validation": {
                    "feasible": true,
                    "interesting": true,
                    "novel": true,
                    "ethical": true,
                    "relevant": true
                }
            }"""
            
            # Create the user message with the research area and constraints
            user_message = f"""Please help me formulate a research question for the following area:
            Research Area: {input_data.research_area}
            Constraints: {input_data.constraints}
            
            Please ensure the question meets the FINER criteria and provide a detailed analysis."""
            
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
                agent_response = AgentResponse(**response_data)
                
                # Convert to FormulateQuestionOutput format
                return FormulateQuestionOutput(
                    question=Question(
                        question=agent_response.question.question,
                        sub_questions=agent_response.question.sub_questions
                    ),
                    validation=agent_response.validation.model_dump()
                )
            except (json.JSONDecodeError, KeyError) as e:
                raise ValueError(f"Invalid response format: {str(e)}")
            
        except TimeoutError:
            raise  # Re-raise TimeoutError without wrapping
        except Exception as e:
            raise RuntimeError(f"Failed to formulate question: {str(e)}") from e

# # Example usage:

# async def main():
#     result = await formulate_question(
#         research_area="quantum computing applications in cryptography",
#         constraints={
#             "time_frame": "2020-2024",
#             "focus_areas": ["post-quantum cryptography", "quantum key distribution"],
#             "scope": "theoretical and experimental studies"
#         }
#     )
#     print(f"Research Question: {result.question.question}")
#     print(f"Sub-questions: {result.question.sub_questions}")
#     print(f"Validation: {result.validation}")

# if __name__ == "__main__":
#     asyncio.run(main())
