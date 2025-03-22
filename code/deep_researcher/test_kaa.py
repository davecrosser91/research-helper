import asyncio
from openai import OpenAI
from deep_researcher.research_agents.keyword_analysis_agent import KeywordAnalysisAgent

async def main():
    # Create an instance of the Keyword Analysis Agent with OpenAI client
    client = OpenAI()  # Make sure you have OPENAI_API_KEY in your environment
    agent = KeywordAnalysisAgent(client=client)
    
    # Test query
    research_question = "How do modifications in transformer architecture designs affect performance optimization and application outcomes in current natural language processing tasks?"
    context = {
        "field": "natural language processing",
        "focus_areas": ["transformer architectures", "performance optimization", "applications"],
        "timeframe": "current"
    }
    
    # Get search strategy
    try:
        result = await agent.analyze(research_question, context)
        
        # Print the results
        print("\nKeywords:")
        for keyword in result.keywords:
            print(f"- {keyword}")
            
        print("\nBoolean Search Combinations:")
        for combo in result.combinations:
            print(f"- {combo}")
            
        print("\nSearch Constraints:")
        for key, value in result.constraints.items():
            print(f"{key}: {value}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 