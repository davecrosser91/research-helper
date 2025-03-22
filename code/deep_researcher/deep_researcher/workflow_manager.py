from typing import Optional, List, Dict, Any
from .models.base import ResearchQuestion, SearchStrategy, PaperResult, WorkflowState
from .research_agents.rqa import ResearchQuestionAgent
from .research_agents.kaa import KeywordAnalysisAgent
from .research_agents.axa import ArxivSearchAgent
from .research_agents.asa import AbstractScreeningAgent

class ResearchWorkflowManager:
    def __init__(self):
        self.current_state: Optional[WorkflowState] = None
        self.history: List[WorkflowState] = []
        
        # Initialize agents
        self.rqa = ResearchQuestionAgent()
        self.kaa = KeywordAnalysisAgent()
        self.axa = ArxivSearchAgent()
        self.asa = AbstractScreeningAgent()
        
        # State storage
        self.research_questions: Optional[ResearchQuestion] = None
        self.search_strategy: Optional[SearchStrategy] = None
        self.paper_results: List[PaperResult] = []
    
    def save_state(self, step: str, data: Any) -> WorkflowState:
        """Save current state and add to history"""
        state = WorkflowState(step=step, data=data)
        self.current_state = state
        self.history.append(state)
        return state
    
    async def formulate_questions(self, research_idea: str) -> WorkflowState:
        """Step 1: Research Question Formulation"""
        questions = await self.rqa.formulate(research_idea)
        return self.save_state("questions", questions)
    
    async def analyze_keywords(self, questions: ResearchQuestion) -> WorkflowState:
        """Step 2: Keyword Analysis"""
        strategy = await self.kaa.analyze(questions)
        return self.save_state("keywords", strategy)
    
    async def search_papers(self, strategy: SearchStrategy) -> WorkflowState:
        """Step 3: Paper Search"""
        papers = await self.axa.search(strategy)
        return self.save_state("papers", papers)
    
    async def screen_abstracts(self, papers: List[PaperResult]) -> WorkflowState:
        """Step 4: Abstract Screening"""
        ranked_papers = await self.asa.screen(papers)
        return self.save_state("screening", ranked_papers)
    
    async def start_workflow(self, research_idea: str) -> WorkflowState:
        """Start the workflow with a research idea"""
        return await self.formulate_questions(research_idea)
    
    async def continue_workflow(self) -> Optional[WorkflowState]:
        """Continue to next step based on current state"""
        if not self.current_state:
            return None
            
        if self.current_state.step == "questions":
            return await self.analyze_keywords(self.current_state.data)
        elif self.current_state.step == "keywords":
            return await self.search_papers(self.current_state.data)
        elif self.current_state.step == "papers":
            return await self.screen_abstracts(self.current_state.data)
        elif self.current_state.step == "screening":
            return None  # Workflow complete
            
        return None
    
    async def modify_current_step(self, modifications: Dict[str, Any]) -> WorkflowState:
        """Apply user modifications to current step"""
        if not self.current_state:
            raise ValueError("No current state to modify")
            
        # Apply modifications based on step type
        data = self.current_state.data
        if isinstance(data, ResearchQuestion):
            data.main_question = modifications.get("main_question", data.main_question)
            data.sub_questions = modifications.get("sub_questions", data.sub_questions)
        elif isinstance(data, SearchStrategy):
            data.keywords = modifications.get("keywords", data.keywords)
            data.combinations = modifications.get("combinations", data.combinations)
        elif isinstance(data, list) and all(isinstance(p, PaperResult) for p in data):
            # Handle paper list modifications
            for paper in data:
                if paper.paper_id in modifications:
                    paper.user_reviewed = True
                    paper.relevance_score = modifications[paper.paper_id]
                    
        self.current_state.modified_by_user = True
        return self.current_state
    
    def go_back(self) -> Optional[WorkflowState]:
        """Go back to previous state"""
        if len(self.history) < 2:
            return None
            
        self.history.pop()  # Remove current state
        self.current_state = self.history[-1]  # Set previous state as current
        return self.current_state
    
    def get_final_results(self) -> List[PaperResult]:
        """Get final ranked papers"""
        if not self.current_state or self.current_state.step != "screening":
            raise ValueError("Workflow not completed")
            
        return sorted(
            self.current_state.data,
            key=lambda p: p.relevance_score or 0,
            reverse=True
        ) 