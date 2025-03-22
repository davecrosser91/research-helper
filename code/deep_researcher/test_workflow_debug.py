import asyncio
import logging
from openai import OpenAI
from deep_researcher.research_agents.workflow import SystematicReviewWorkflow

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Enable debug logging for all relevant modules
logging.getLogger('deep_researcher').setLevel(logging.DEBUG)
logging.getLogger('arxiv').setLevel(logging.DEBUG)
logging.getLogger('httpx').setLevel(logging.DEBUG)

async def main():
    # Create logger for this test
    logger = logging.getLogger('workflow_test')
    logger.setLevel(logging.DEBUG)
    
    # Create an instance of the workflow with OpenAI client
    logger.debug("Initializing OpenAI client and workflow")
    client = OpenAI()
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
        
        logger.debug(f"Starting workflow with research area: {research_area}")
        logger.debug(f"Constraints: {constraints}")
        
        print("\n🚀 Starting systematic review workflow...")
        result = await workflow.start_review(research_area, constraints)
        
        # Print Research Question Results
        logger.debug("Printing research question results")
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
        logger.debug("Printing search strategy results")
        print("\n🔍 === Search Strategy Results ===\n")
        print("Keywords:")
        for keyword in result.search_strategy.keywords:
            print(f"- {keyword}")
        print("\nBoolean Search Combinations:")
        for combo in result.search_strategy.combinations:
            print(f"- {combo}")
            
        # Print Screening Results
        if result.screened_papers:
            logger.debug("Printing screening results")
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
                    
        logger.debug("Workflow test completed successfully")
        print("\n✅ Workflow test completed successfully!")
            
    except Exception as e:
        logger.error(f"Error during workflow test: {str(e)}", exc_info=True)
        print(f"\n❌ Error during workflow test: {str(e)}")
        raise

if __name__ == "__main__":
    asyncio.run(main()) 