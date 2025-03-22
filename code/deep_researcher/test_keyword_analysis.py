import asyncio
import json
from openai import OpenAI
from deep_researcher.research_agents.keyword_analysis_agent import KeywordAnalysisAgent
from deep_researcher.research_agents.types import SearchStrategy

async def test_keyword_analysis():
    print("Starting Keyword Analysis Test")
    
    # Test parameters
    research_question = "What are the recent advancements in transformer architectures for natural language processing?"
    context = {
        "min_year": 2020,
        "max_year": 2024,
        "categories": ["cs.CL", "cs.AI", "cs.LG"]
    }
    
    try:
        # Initialize the agent
        agent = KeywordAnalysisAgent(client=OpenAI())
        
        # Run the analysis
        print(f"\nAnalyzing research question: {research_question}")
        print(f"Context: {json.dumps(context, indent=2)}")
        
        result: SearchStrategy = await agent.analyze(research_question, context)
        
        # Print results
        print("\nAnalysis Results:")
        print("Keywords:")
        for keyword in result.keywords:
            print(f"  - {keyword}")
        
        print("\nSearch Combinations:")
        for combo in result.combinations:
            print(f"  - {combo}")
        
        print("\nConstraints:")
        print(json.dumps(result.constraints, indent=2))
        
        return result
        
    except Exception as e:
        print(f"\nError during keyword analysis: {str(e)}")
        raise

async def main():
    try:
        await test_keyword_analysis()
    except Exception as e:
        print(f"\nTest failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 