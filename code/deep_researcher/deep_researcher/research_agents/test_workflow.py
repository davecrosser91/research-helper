import asyncio
import json
from datetime import datetime, timedelta
from workflow_orchestrator import workflow_orchestrator

async def test_workflow():
    # Example research request
    research_input = {
        "description": """
        I'm interested in understanding how quantum computing can be applied to optimize 
        machine learning algorithms, particularly in the context of solving complex optimization 
        problems that are intractable for classical computers. I want to focus on recent 
        practical applications and experimental results rather than purely theoretical work.
        """,
        "field": "quantum machine learning",
        "time_range": {
            "start": (datetime.now() - timedelta(years=2)).strftime("%Y-%m-%d"),
            "end": datetime.now().strftime("%Y-%m-%d")
        },
        "categories": ["quant-ph", "cs.AI", "cs.LG"]
    }
    
    try:
        print("Starting research workflow...")
        print("\nResearch Input:")
        print(f"Field: {research_input['field']}")
        print(f"Time Range: {research_input['time_range']['start']} to {research_input['time_range']['end']}")
        print(f"Categories: {', '.join(research_input['categories'])}")
        print("\nDescription:")
        print(research_input['description'].strip())
        
        # Execute workflow
        result = await workflow_orchestrator.run(research_input)
        data = json.loads(result)
        
        # Print results in a structured format
        print("\n" + "="*80)
        print("RESEARCH WORKFLOW RESULTS")
        print("="*80)
        
        print("\n1. Research Question:")
        print(f"Main Question: {data['research_question']}")
        print("\nSub-questions:")
        for i, q in enumerate(data['sub_questions'], 1):
            print(f"{i}. {q}")
        
        print("\n2. Search Strategy:")
        print(f"Query: {data['search_strategy']['query']}")
        print("\nKeywords:")
        for key, value in data['search_strategy']['keywords'].items():
            print(f"- {key}: {value}")
        
        print("\n3. Statistics:")
        stats = data['statistics']
        print(f"Total papers found: {stats['total_papers_found']}")
        print(f"Relevant papers: {stats['relevant_papers']}")
        print(f"High relevance: {stats['high_relevance']}")
        print(f"Medium relevance: {stats['medium_relevance']}")
        
        print("\nTop Themes:")
        for theme in stats['top_themes']:
            print(f"- {theme}")
        
        print("\n4. Relevant Papers:")
        for i, paper in enumerate(data['relevant_papers'], 1):
            print(f"\nPaper {i}:")
            print(f"Title: {paper['title']}")
            print(f"Authors: {', '.join(paper['authors'])}")
            print(f"Relevance: {paper['relevance_score']}")
            print(f"Methodology: {paper['methodology']}")
            print(f"URL: {paper['url']}")
            print(f"Themes: {', '.join(paper['themes'])}")
            print(f"Detailed Review Recommended: {'Yes' if paper['detailed_review_recommended'] else 'No'}")
            print("-" * 40)
        
        print("\nWorkflow completed successfully!")
        
    except Exception as e:
        print(f"Error during workflow execution: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_workflow()) 