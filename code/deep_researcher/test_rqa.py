import asyncio
from openai import OpenAI
from deep_researcher.research_agents.research_question_agent import ResearchQuestionAgent
from deep_researcher.research_agents.types import FormulateQuestionInput

async def main():
    # Create an instance of the Research Question Agent with OpenAI client
    client = OpenAI()  # Make sure you have OPENAI_API_KEY in your environment
    agent = ResearchQuestionAgent(client=client)
    
    # Test query
    research_area = "transformer architectures in natural language processing"
    input_data = FormulateQuestionInput(
        research_area=research_area,
        constraints={
            "time_frame": "current",
            "focus_areas": ["architecture design", "performance optimization", "applications"],
            "scope": "theoretical and empirical studies"
        }
    )
    
    # Get research questions
    try:
        result = await agent.formulate_question(input_data)
        
        # Print the results
        print("\nMain Research Question:")
        print(result.question.question)
        print("\nSub Questions:")
        for i, q in enumerate(result.question.sub_questions, 1):
            print(f"{i}. {q}")
        print("\nValidation:")
        for criterion, value in result.validation.items():
            print(f"{criterion}: {value}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 