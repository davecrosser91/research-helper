import asyncio
from openai import OpenAI
from deep_researcher.research_agents.workflow import SystematicReviewWorkflow

async def main():
    # Create an instance of the workflow with OpenAI client
    client = OpenAI()  # Make sure you have OPENAI_API_KEY in your environment
    workflow = SystematicReviewWorkflow(openai_client=client)
    
    # Test query
    research_area = "transformer architectures in natural language processing"
    constraints = {
        "time_frame": "current",
        "focus_areas": ["architecture design", "performance optimization", "applications"],
        "scope": "theoretical and empirical studies"
    }
    
    # Run the workflow
    try:
        result = await workflow.start_review(research_area, constraints)
        
        # Print Research Question Results
        print("\n=== Research Question Results ===")
        print("\nMain Question:")
        print(result["research_question"].question.question)
        print("\nSub Questions:")
        for i, q in enumerate(result["research_question"].question.sub_questions, 1):
            print(f"{i}. {q}")
        print("\nValidation:")
        for criterion, value in result["research_question"].validation.items():
            print(f"{criterion}: {value}")
            
        # Print Search Strategy Results
        print("\n=== Search Strategy Results ===")
        print("\nKeywords:")
        for keyword in result["search_strategy"].keywords:
            print(f"- {keyword}")
        print("\nBoolean Search Combinations:")
        for combo in result["search_strategy"].combinations:
            print(f"- {combo}")
        print("\nSearch Constraints:")
        for key, value in result["search_strategy"].constraints.items():
            print(f"{key}: {value}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 