import asyncio
from deep_researcher.research_agents.keyword_agent import KeywordAgent, KeywordAnalysisInput

async def main():
    print("\n🔍 Research Topic Keyword Analyzer 🔍")
    print("====================================")
    
    # Initialize the agent
    agent = KeywordAgent()
    
    while True:
        # Get user input
        print("\nEnter your research topic (or 'quit' to exit):")
        topic = input("> ").strip()
        
        if topic.lower() == 'quit':
            print("\n👋 Thank you for using the Keyword Analyzer!")
            break
        
        print("\nEnter field context (optional, press Enter to skip):")
        print("Example: computer science, biology, psychology, etc.")
        context = input("> ").strip()
        
        print("\nEnter focus areas (optional, comma-separated, press Enter to skip):")
        print("Example: machine learning, neural networks, deep learning")
        focus_areas_input = input("> ").strip()
        focus_areas = [area.strip() for area in focus_areas_input.split(",")] if focus_areas_input else None
        
        # Create input data
        input_data = KeywordAnalysisInput(
            research_topic=topic,
            field_context=context if context else None,
            focus_areas=focus_areas
        )
        
        try:
            print("\n🤔 Analyzing keywords...")
            result = await agent.analyze_keywords(input_data)
            
            print("\n📝 Analysis Results:")
            print("==================")
            
            print("\n🎯 Primary Keywords:")
            for keyword in result.primary_keywords:
                print(f"- {keyword}")
            
            print("\n🔄 Secondary Keywords:")
            for keyword in result.secondary_keywords:
                print(f"- {keyword}")
            
            print("\n📚 Technical Terms:")
            for term in result.technical_terms:
                print(f"- {term}")
                if term in result.explanations:
                    print(f"  ℹ️ {result.explanations[term]}")
            
            print("\n🔗 Related Concepts:")
            for concept in result.related_concepts:
                print(f"- {concept}")
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try again with a different input.")

if __name__ == "__main__":
    asyncio.run(main()) 