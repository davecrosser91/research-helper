import asyncio
from openai import OpenAI
from research_agents.workflow import SystematicReviewWorkflow

async def main():
    # Create an instance of the workflow with OpenAI client
    client = OpenAI()  # Make sure you have OPENAI_API_KEY in your environment
    workflow = SystematicReviewWorkflow(client)
    
    try:
        # Define research area and constraints
        research_area = "transformer architectures in natural language processing"
        constraints = {
            "max_papers": 5,
            "min_year": 2020,
            "max_year": 2024,
            "min_citations": 0
        }
        
        print("\n🚀 Starting systematic review workflow...")
        result = await workflow.start_review(research_area, constraints)
        
        # Print Research Question Results
        print("\n📝 === Research Question Results ===\n")
        print("Main Question:")
        print(result.research_question.question.question)
        print("\nSub Questions:")
        for i, q in enumerate(result.research_question.question.sub_questions, 1):
            print(f"{i}. {q}")
        print("\nValidation:")
        for k, v in result.research_question.validation.items():
            print(f"{k}: {'✅' if v else '❌'}")
        
        # Print Search Strategy Results
        print("\n🔍 === Search Strategy Results ===\n")
        print("Keywords:")
        for keyword in result.search_strategy.keywords:
            print(f"- {keyword}")
        print("\nBoolean Search Combinations:")
        for combo in result.search_strategy.combinations:
            print(f"- {combo}")
            
        # Print Screening Results
        if result.screened_papers:
            print("\n📚 === Paper Screening Results ===")
            for batch in result.screened_papers:
                print(f"\nBatch {batch['batch_id']}:")
                print("\nStatistics:")
                for stat, value in batch['batch_statistics'].items():
                    print(f"- {stat}: {value}")
                
                print("\nPapers by Priority:")
                for paper in sorted(batch['papers'], key=lambda x: x['priority_rank']):
                    print(f"\nRank {paper['priority_rank']}:")
                    print(f"Relevance Score: {paper['relevance_score']:.2f}")
                    print(f"Rationale: {paper['rationale']}")
                    print("-" * 80)
                    
        print("\n✅ Workflow test completed successfully!")
            
    except Exception as e:
        print(f"\n❌ Error during workflow test: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main())