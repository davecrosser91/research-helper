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
    
    # Test papers
    papers = [
        {
            "paper_id": "2103.12345",
            "title": "Efficient Transformer Architectures for NLP Tasks",
            "authors": ["John Doe", "Jane Smith"],
            "abstract": """
            This paper presents novel modifications to transformer architectures that significantly improve 
            their performance on various NLP tasks. We introduce a new attention mechanism that reduces 
            computational complexity while maintaining accuracy. Experimental results show 30% faster 
            training and inference times with comparable or better results on standard benchmarks.
            """,
            "metadata": {"year": 2023, "citations": 45}
        },
        {
            "paper_id": "2104.67890",
            "title": "Survey of Transformer Models in NLP",
            "authors": ["Alice Johnson", "Bob Wilson"],
            "abstract": """
            We provide a comprehensive survey of transformer architectures in natural language processing.
            The paper covers recent developments, optimization techniques, and applications across different
            domains. We analyze performance trends and identify promising future research directions.
            """,
            "metadata": {"year": 2023, "citations": 120}
        }
    ]
    
    # Run the workflow
    try:
        result = await workflow.start_review(research_area, constraints, papers)
        
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
            
        # Print Screening Results
        if "screened_papers" in result:
            print("\n=== Paper Screening Results ===")
            for paper in result["screened_papers"]:
                print(f"\nPaper: {paper.title}")
                print(f"Relevance Score: {paper.relevance_score}")
                print("\nInclusion Criteria:")
                for criterion, met in paper.inclusion_criteria.items():
                    print(f"- {criterion}: {'✓' if met else '✗'}")
                print(f"Priority Rank: {paper.priority_rank}")
                print(f"Rationale: {paper.metadata.get('rationale', 'No rationale provided')}")
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main()) 