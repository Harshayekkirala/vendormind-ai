import time
import asyncio
from typing import Dict, Any, List
from app.agents.base import BaseAgent
from app.schemas.agent_outputs import ProcurementDecisionState, AgentStatusEnum, AgentExecutionState

# Import Extraction Agents
from app.agents.extraction.email_agent import EmailAgent
from app.agents.extraction.quote_agent import QuoteAgent
from app.agents.extraction.contract_agent import ContractAgent
from app.agents.extraction.meeting_agent import MeetingAgent

# Import Decision Agents
from app.agents.decision.rag_agent import RAGAgent
from app.agents.decision.memory_agent import MemoryAgent
from app.agents.decision.risk_agent import RiskAgent
from app.agents.decision.missing_info_agent import MissingInfoAgent
from app.agents.decision.reasoning_agent import ReasoningAgent
from app.agents.decision.action_agent import ActionAgent

class PlannerAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Planner Agent",
            description="Orchestrates the execution of all extraction and decision agents based on uploaded documentation."
        )
        # Initialize instances of all sub-agents
        self.extraction_agents = {
            "email": EmailAgent(),
            "quotation": QuoteAgent(),
            "contract": ContractAgent(),
            "meeting_notes": MeetingAgent()
        }
        self.decision_agents = [
            RAGAgent(),
            MemoryAgent(),
            RiskAgent(),
            MissingInfoAgent(),
            ReasoningAgent(),
            ActionAgent()
        ]

    async def run(self, context: Dict[str, Any], *args, **kwargs) -> ProcurementDecisionState:
        session_id = context.get("session_id", "session_default")
        uploaded_files = context.get("uploaded_files", [])
        
        # Determine which extraction agents should be run based on uploaded file types
        # (For this mock/scaffold, if no file types are explicitly specified, we default to running everything)
        active_doc_types = context.get("doc_types_to_process", ["email", "quotation", "contract", "meeting_notes"])
        
        state = ProcurementDecisionState(
            session_id=session_id,
            uploaded_files=uploaded_files,
            agent_timeline=[]
        )
        
        # Populate session state timeline with PENDING status for agents we plan to run
        context["agent_timeline"] = state.agent_timeline
        
        for doc_type in active_doc_types:
            if doc_type in self.extraction_agents:
                self.extraction_agents[doc_type].get_timeline_state(context)
                
        for agent in self.decision_agents:
            agent.get_timeline_state(context)

        # --- Phase 1: Run Extraction Agents ---
        # We can run these in parallel since they don't depend on each other's outputs
        extraction_tasks = []
        for doc_type in active_doc_types:
            if doc_type in self.extraction_agents:
                agent = self.extraction_agents[doc_type]
                extraction_tasks.append(self._run_and_bind(agent, context, doc_type, state))
        
        if extraction_tasks:
            await asyncio.gather(*extraction_tasks)

        # --- Phase 2: Run Decision Agents sequentially ---
        # These are run sequentially because they synthesize results (e.g. Reasoning needs RAG/Risk/Memory, Action needs Reasoning)
        for agent in self.decision_agents:
            # Short sleep to simulate processing time / allow frontend to see the progression
            await asyncio.sleep(0.5)
            
            exec_result = await agent.execute(context)
            if exec_result["success"]:
                # Bind results to the state object
                val = exec_result["data"]
                if agent.name == "RAG Agent":
                    state.rag_checks = val
                elif agent.name == "Memory Agent":
                    state.memory_data = val
                elif agent.name == "Risk Agent":
                    state.risk_assessment = val
                elif agent.name == "Missing Info Agent":
                    state.missing_info = val
                elif agent.name == "Reasoning Agent":
                    state.reasoning = val
                elif agent.name == "Action Agent":
                    state.next_best_action = val
            else:
                # If a decision agent fails, log it but continue the chain (or handle accordingly)
                print(f"Error executing agent {agent.name}: {exec_result.get('error')}")

        return state

    async def _run_and_bind(self, agent: BaseAgent, context: Dict[str, Any], doc_type: str, state: ProcurementDecisionState):
        # Add a small random delay to simulate extraction time
        await asyncio.sleep(0.3)
        
        exec_result = await agent.execute(context)
        if exec_result["success"]:
            val = exec_result["data"]
            if doc_type == "email":
                state.email_data = val
            elif doc_type == "quotation":
                state.quote_data = val
            elif doc_type == "contract":
                state.contract_data = val
            elif doc_type == "meeting_notes":
                state.meeting_data = val
        else:
            print(f"Error executing agent {agent.name}: {exec_result.get('error')}")
