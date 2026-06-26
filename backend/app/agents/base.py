import time
from abc import ABC, abstractmethod
from typing import Any, Dict
from app.schemas.agent_outputs import AgentStatusEnum, AgentExecutionState

class BaseAgent(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def run(self, context: Dict[str, Any], *args, **kwargs) -> Any:
        """
        Execute the agent's main logic.
        :param context: A dictionary containing the accumulated state/documents of the procurement session.
        :return: The structured output of the agent.
        """
        pass

    async def execute(self, context: Dict[str, Any], *args, **kwargs) -> Dict[str, Any]:
        """
        Wrapper that handles timing, status, and error handling for UI updates.
        """
        start_time = time.time()
        execution_state = AgentExecutionState(
            agent_name=self.name,
            status=AgentStatusEnum.RUNNING
        )
        
        # Add the agent to the timeline list in context if present
        if "agent_timeline" not in context:
            context["agent_timeline"] = []
        
        # Check if already added, if not, add it
        timeline = context["agent_timeline"]
        existing = next((s for s in timeline if s.agent_name == self.name), None)
        if not existing:
            timeline.append(execution_state)
            existing = execution_state
        else:
            existing.status = AgentStatusEnum.RUNNING

        try:
            result = await self.run(context, *args, **kwargs)
            duration = int((time.time() - start_time) * 1000)
            
            existing.status = AgentStatusEnum.COMPLETED
            existing.duration_ms = duration
            
            return {
                "success": True,
                "data": result,
                "duration_ms": duration
            }
        except Exception as e:
            duration = int((time.time() - start_time) * 1000)
            existing.status = AgentStatusEnum.FAILED
            existing.duration_ms = duration
            existing.error_message = str(e)
            
            return {
                "success": False,
                "error": str(e),
                "duration_ms": duration
            }
        
    def get_timeline_state(self, context: Dict[str, Any]) -> AgentExecutionState:
        timeline = context.get("agent_timeline", [])
        existing = next((s for s in timeline if s.agent_name == self.name), None)
        if not existing:
            existing = AgentExecutionState(agent_name=self.name, status=AgentStatusEnum.PENDING)
            timeline.append(existing)
        return existing
