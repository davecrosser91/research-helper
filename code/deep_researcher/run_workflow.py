import asyncio
from openai import OpenAI
from research_agents.workflow import SystematicReviewWorkflow

async def run_workflow():
    """Run the systematic review workflow with default parameters."""
    print("\n🚀 Starting systematic review workflow...")
    
    # Initialize workflow
    client = OpenAI()
    workflow = SystematicReviewWorkflow(client)
    
    # Set research parameters
    research_area = "transformer architectures in natural language processing"
    constraints = {
        "publication_years": [2020, 2025],
        "max_results":5,
        "batch_size": 5,
        "max_combinations": 5,
        "methodology_focus": ["experimental", "theoretical"]
    }
    
    try:
        # Execute workflow
        result = await workflow.start_review(research_area, constraints)
        
        # Print final results
        print("\n✅ Workflow completed successfully!")
        print(f"\nResearch Question: {result.research_question.question.question}")
        
        if result.research_question.question.sub_questions:
            print("\nSub-questions:")
            for i, q in enumerate(result.research_question.question.sub_questions, 1):
                print(f"{i}. {q}")
        
        print(f"\nFound {len(result.papers)} papers in total")
        
        if result.screened_papers:
            total_relevant = sum(
                len([p for p in batch["papers"] if p["relevance_score"] > 0.5])
                for batch in result.screened_papers
            )
            print(f"After screening: {total_relevant} highly relevant papers")
            
    except Exception as e:
        print(f"\n❌ Error during workflow test: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(run_workflow()) 