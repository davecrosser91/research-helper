from typing import Dict, List, Optional, Type, TypeVar
from datetime import datetime
import asyncio
import logging
import uuid

from ..deep_researcher.research_agents.types import (
    Message, WorkflowState, WorkflowContext,
    AgentResult, AgentError, MessageType
)
from .base_agent import BaseAgent, RecoverableError, UnrecoverableError

T = TypeVar('T')

class ResearchOrchestrator:
    """Orchestrates the systematic review workflow and agent communication."""
    
    def __init__(self):
        self.agents: Dict[str, BaseAgent] = {}
        self.workflow_contexts: Dict[str, WorkflowContext] = {}
        self.message_queue: asyncio.Queue[Message] = asyncio.Queue()
        self.logger = logging.getLogger("orchestrator")
        
    def register_agent(self, agent: BaseAgent):
        """Register an agent with the orchestrator."""
        self.agents[agent.name] = agent
        self.logger.info(f"Registered agent: {agent.name}")
        
    async def start_workflow(
        self,
        research_area: str,
        constraints: Dict[str, str]
    ) -> str:
        """Start a new systematic review workflow."""
        workflow_id = str(uuid.uuid4())
        
        context = WorkflowContext(
            workflow_id=workflow_id,
            state=WorkflowState.INITIALIZING,
            start_time=datetime.utcnow(),
            research_area=research_area,
            constraints=constraints,
            metadata={}
        )
        
        self.workflow_contexts[workflow_id] = context
        self.logger.info(f"Started workflow: {workflow_id}")
        
        # Initialize the workflow with research question formulation
        await self.transition_workflow_state(
            workflow_id,
            WorkflowState.QUESTION_FORMULATION
        )
        
        return workflow_id
    
    async def transition_workflow_state(
        self,
        workflow_id: str,
        new_state: WorkflowState
    ):
        """Transition a workflow to a new state."""
        context = self.workflow_contexts[workflow_id]
        old_state = context.state
        context.state = new_state
        
        self.logger.info(
            f"Workflow {workflow_id} state change: {old_state} -> {new_state}"
        )
        
        # Handle state-specific logic
        if new_state == WorkflowState.QUESTION_FORMULATION:
            await self._start_question_formulation(workflow_id)
        elif new_state == WorkflowState.KEYWORD_ANALYSIS:
            await self._start_keyword_analysis(workflow_id)
        elif new_state == WorkflowState.SEARCH_EXECUTION:
            await self._start_search_execution(workflow_id)
        elif new_state == WorkflowState.ABSTRACT_SCREENING:
            await self._start_abstract_screening(workflow_id)
    
    async def process_message(self, message: Message):
        """Process a message by routing it to the appropriate agent."""
        try:
            if message.recipient not in self.agents:
                raise ValueError(f"Unknown recipient: {message.recipient}")
            
            agent = self.agents[message.recipient]
            context = self.workflow_contexts[message.metadata["workflow_id"]]
            
            # Validate and process the message
            if await agent.validate_input(message):
                result = await agent.process_message(message, context)
                if await agent.validate_output(result):
                    await self._handle_agent_result(result, message, context)
                else:
                    raise ValueError("Invalid agent output")
            else:
                raise ValueError("Invalid message input")
                
        except Exception as e:
            await self._handle_error(e, message)
    
    async def _handle_agent_result(
        self,
        result: AgentResult,
        message: Message,
        context: WorkflowContext
    ):
        """Handle the result from an agent's message processing."""
        if result.success:
            # Create response message if needed
            if message.reply_to:
                response = Message(
                    id=str(uuid.uuid4()),
                    type=MessageType.RESPONSE,
                    sender=message.recipient,
                    recipient=message.sender,
                    content=result.data,
                    timestamp=datetime.utcnow(),
                    correlation_id=message.correlation_id,
                    reply_to=message.id,
                    metadata={"workflow_id": context.workflow_id}
                )
                await self.message_queue.put(response)
            
            # Check for workflow state transition
            if result.metadata.get("next_state"):
                await self.transition_workflow_state(
                    context.workflow_id,
                    result.metadata["next_state"]
                )
        else:
            await self._handle_error(
                Exception(result.error),
                message
            )
    
    async def _handle_error(self, error: Exception, message: Message):
        """Handle errors in message processing."""
        self.logger.error(
            f"Error processing message {message.id}: {str(error)}"
        )
        
        if isinstance(error, RecoverableError):
            # Implement retry logic
            pass
        elif isinstance(error, UnrecoverableError):
            # Update workflow state to error
            context = self.workflow_contexts[message.metadata["workflow_id"]]
            context.state = WorkflowState.ERROR
            context.metadata["error"] = str(error)
    
    async def run(self):
        """Main loop for processing messages."""
        while True:
            message = await self.message_queue.get()
            await self.process_message(message)
            self.message_queue.task_done()
    
    # Workflow state transition handlers
    async def _start_question_formulation(self, workflow_id: str):
        """Initialize the question formulation phase."""
        context = self.workflow_contexts[workflow_id]
        message = Message(
            id=str(uuid.uuid4()),
            type=MessageType.COMMAND,
            sender="orchestrator",
            recipient="research_question_agent",
            content={
                "research_area": context.research_area,
                "constraints": context.constraints
            },
            timestamp=datetime.utcnow(),
            metadata={"workflow_id": workflow_id}
        )
        await self.message_queue.put(message)
    
    async def _start_keyword_analysis(self, workflow_id: str):
        """Initialize the keyword analysis phase."""
        pass  # Similar to _start_question_formulation
    
    async def _start_search_execution(self, workflow_id: str):
        """Initialize the search execution phase."""
        pass  # Similar to _start_question_formulation
    
    async def _start_abstract_screening(self, workflow_id: str):
        """Initialize the abstract screening phase."""
        pass  # Similar to _start_question_formulation 