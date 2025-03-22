import asyncio
from deep_researcher.research_agents.research_question_agent import ResearchQuestionAgent
from deep_researcher.research_agents.types import FormulateQuestionInput

async def main():
    print("\n🔍 Research Question Generator 🔍")
    print("================================")
    
    # Initialize the agent
    agent = ResearchQuestionAgent()
    
    while True:
        # Get user input
        print("\nEnter your research area (or 'quit' to exit):")
        research_area = input("> ").strip()
        
        if research_area.lower() == 'quit':
            print("\n👋 Thank you for using the Research Question Generator!")
            break
        
        print("\nEnter any constraints (optional, press Enter to skip):")
        print("Example: time period, focus areas, methodology, etc.")
        constraints = input("> ").strip()
        
        # Create input data
        input_data = FormulateQuestionInput(
            research_area=research_area,
            constraints={"user_constraints": constraints} if constraints else {}
        )
        
        try:
            print("\n🤔 Generating research question...")
            result = await agent.formulate_question(input_data)
            
            print("\n📝 Results:")
            print("===========")
            print(f"\nMain Research Question:\n{result.question.question}")
            
            if result.question.sub_questions:
                print("\nSub-questions:")
                for i, sq in enumerate(result.question.sub_questions, 1):
                    print(f"{i}. {sq}")
            
            print("\nScope:")
            for key, value in result.question.scope.items():
                print(f"- {key}: {value}")
            
            print("\nFINER Criteria Validation:")
            for criterion, value in result.validation.items():
                status = "✅" if value else "❌"
                print(f"{status} {criterion.capitalize()}")
                
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try again with a different input.")

if __name__ == "__main__":
    asyncio.run(main()) 