import asyncio
import typer
from rich.console import Console
from rich.prompt import Prompt, Confirm
from rich.table import Table
from typing import Optional, Dict, Any

from .workflow_manager import ResearchWorkflowManager
from .models.base import ResearchQuestion, SearchStrategy, PaperResult

app = typer.Typer()
console = Console()

def display_research_questions(questions: ResearchQuestion):
    """Display research questions with formatting"""
    console.print("\n[bold blue]Research Questions:[/bold blue]")
    console.print(f"Main Question: {questions.main_question}")
    console.print("\nSub Questions:")
    for i, q in enumerate(questions.sub_questions, 1):
        console.print(f"{i}. {q}")
    console.print(f"\nValidation Score: {questions.validation_score:.2f}")

def display_search_strategy(strategy: SearchStrategy):
    """Display search strategy with formatting"""
    console.print("\n[bold blue]Search Strategy:[/bold blue]")
    console.print("\nKeywords:")
    for kw in strategy.keywords:
        console.print(f"• {kw}")
    console.print("\nSearch Combinations:")
    for comb in strategy.combinations:
        console.print(f"• {comb}")

def display_papers(papers: list[PaperResult]):
    """Display papers in a table"""
    table = Table(title="Paper Results")
    table.add_column("ID", style="cyan")
    table.add_column("Title", style="magenta")
    table.add_column("Score", justify="right", style="green")
    table.add_column("Reviewed", justify="center")
    
    for paper in papers:
        score = f"{paper.relevance_score:.2f}" if paper.relevance_score is not None else "N/A"
        reviewed = "✓" if paper.user_reviewed else ""
        table.add_row(paper.paper_id, paper.title, score, reviewed)
    
    console.print(table)

def get_user_modifications(state_data: Any) -> Dict[str, Any]:
    """Get user modifications based on data type"""
    modifications = {}
    
    if isinstance(state_data, ResearchQuestion):
        if Confirm.ask("Modify main question?"):
            modifications["main_question"] = Prompt.ask("Enter new main question")
        if Confirm.ask("Modify sub-questions?"):
            sub_questions = []
            while Confirm.ask("Add sub-question?"):
                sub_questions.append(Prompt.ask("Enter sub-question"))
            modifications["sub_questions"] = sub_questions
            
    elif isinstance(state_data, SearchStrategy):
        if Confirm.ask("Modify keywords?"):
            keywords = []
            while Confirm.ask("Add keyword?"):
                keywords.append(Prompt.ask("Enter keyword"))
            modifications["keywords"] = keywords
            
    elif isinstance(state_data, list) and all(isinstance(p, PaperResult) for p in state_data):
        while Confirm.ask("Rate a paper?"):
            paper_id = Prompt.ask("Enter paper ID")
            score = float(Prompt.ask("Enter relevance score (0-1)"))
            modifications[paper_id] = score
            
    return modifications

async def handle_state(workflow: ResearchWorkflowManager):
    """Handle current workflow state and user interactions"""
    while True:
        state = workflow.current_state
        if not state:
            break
            
        # Display current state
        console.print(f"\n[bold]Current Step: {state.step}[/bold]")
        
        if isinstance(state.data, ResearchQuestion):
            display_research_questions(state.data)
        elif isinstance(state.data, SearchStrategy):
            display_search_strategy(state.data)
        elif isinstance(state.data, list) and all(isinstance(p, PaperResult) for p in state.data):
            display_papers(state.data)
            
        # Get user action
        action = Prompt.ask(
            "What would you like to do?",
            choices=["continue", "modify", "back", "finish"],
            default="continue"
        )
        
        if action == "continue":
            new_state = await workflow.continue_workflow()
            if not new_state:
                break
        elif action == "modify":
            modifications = get_user_modifications(state.data)
            await workflow.modify_current_step(modifications)
        elif action == "back":
            if not workflow.go_back():
                console.print("[red]Cannot go back further[/red]")
        else:  # finish
            break

@app.command()
def main(
    research_idea: Optional[str] = typer.Argument(
        None, help="Initial research idea to start with"
    )
):
    """Start the research workflow"""
    if not research_idea:
        research_idea = Prompt.ask("Please describe your research idea")
        
    workflow = ResearchWorkflowManager()
    
    try:
        asyncio.run(workflow.start_workflow(research_idea))
        asyncio.run(handle_state(workflow))
        
        # Show final results if workflow completed
        if workflow.current_state and workflow.current_state.step == "screening":
            final_papers = workflow.get_final_results()
            console.print("\n[bold green]Final Results:[/bold green]")
            display_papers(final_papers)
            
    except Exception as e:
        console.print(f"[red]Error: {str(e)}[/red]")
        raise typer.Exit(1)

if __name__ == "__main__":
    app() 