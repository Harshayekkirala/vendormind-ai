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

# Import Decision Agents (PRD Renamed: RAG -> PolicyCompliance, Action -> RecommendationExplainability)
from app.agents.decision.rag_agent import PolicyComplianceAgent
from app.agents.decision.memory_agent import MemoryAgent
from app.agents.decision.risk_agent import RiskAgent
from app.agents.decision.missing_info_agent import MissingInfoAgent
from app.agents.decision.reasoning_agent import ReasoningAgent
from app.agents.decision.action_agent import RecommendationExplainabilityAgent

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
            PolicyComplianceAgent(),
            MemoryAgent(),
            RiskAgent(),
            MissingInfoAgent(),
            ReasoningAgent(),
            RecommendationExplainabilityAgent()
        ]

    async def _run_single_vendor(self, context: Dict[str, Any], *args, **kwargs) -> ProcurementDecisionState:
        session_id = context.get("session_id", "session_default")
        uploaded_files = context.get("uploaded_files", [])
        
        # PRD Mandatory checks: Skip extraction agents if the corresponding document content is missing
        active_doc_types = []
        skipped_doc_types = []
        
        content_checks = {
            "email": "email_content",
            "quotation": "quote_content",
            "contract": "contract_content",
            "meeting_notes": "meeting_content"
        }
        
        for doc_type, content_key in content_checks.items():
            if context.get(content_key, "").strip():
                active_doc_types.append(doc_type)
            else:
                skipped_doc_types.append(doc_type)
        
        state = ProcurementDecisionState(
            session_id=session_id,
            uploaded_files=uploaded_files,
            agent_timeline=[]
        )
        
        # Populate session state timeline
        context["agent_timeline"] = state.agent_timeline
        
        # 1. Add active extraction agents as PENDING
        for doc_type in active_doc_types:
            if doc_type in self.extraction_agents:
                self.extraction_agents[doc_type].get_timeline_state(context)
                
        # 2. Add skipped extraction agents as SKIPPED
        for doc_type in skipped_doc_types:
            if doc_type in self.extraction_agents:
                agent = self.extraction_agents[doc_type]
                timeline_state = agent.get_timeline_state(context)
                timeline_state.status = AgentStatusEnum.SKIPPED
                
        # 3. Add decision agents as PENDING
        for agent in self.decision_agents:
            agent.get_timeline_state(context)

        # --- Phase 1: Run Extraction Agents ---
        # Run active extraction tasks in parallel
        extraction_tasks = []
        for doc_type in active_doc_types:
            if doc_type in self.extraction_agents:
                agent = self.extraction_agents[doc_type]
                extraction_tasks.append(self._run_and_bind(agent, context, doc_type, state))
        
        if extraction_tasks:
            await asyncio.gather(*extraction_tasks)

        # --- Phase 2: Run Decision Agents in Parallel where possible ---
        # Map decision agents by their names for quick access
        agents_by_name = {agent.name: agent for agent in self.decision_agents}
        policy_agent = agents_by_name.get("Policy Compliance Agent")
        memory_agent = agents_by_name.get("Memory Agent")
        risk_agent = agents_by_name.get("Risk Agent")
        missing_agent = agents_by_name.get("Missing Info Agent")
        reasoning_agent = agents_by_name.get("Reasoning Agent")
        rec_explain_agent = agents_by_name.get("Recommendation & Explainability Agent")

        async def run_and_bind_decision(agent: BaseAgent):
            await asyncio.sleep(0.02)
            exec_result = await agent.execute(context)
            if exec_result["success"]:
                val = exec_result["data"]
                if agent.name == "Policy Compliance Agent":
                    state.policy_checks = val
                    context["policy_checks"] = val
                elif agent.name == "Memory Agent":
                    state.memory_data = val
                    context["memory_data"] = val
                elif agent.name == "Risk Agent":
                    state.risk_assessment = val
                    context["risk_assessment"] = val
                elif agent.name == "Missing Info Agent":
                    state.missing_info = val
                    context["missing_info"] = val
                elif agent.name == "Reasoning Agent":
                    state.reasoning = val
                    context["reasoning"] = val
                elif agent.name == "Recommendation & Explainability Agent":
                    state.next_best_action = val
                    context["next_best_action"] = val
            else:
                print(f"Error executing agent {agent.name}: {exec_result.get('error')}")

        # Step 2a: Run Policy Compliance and Memory agents in parallel
        tasks_2a = []
        if policy_agent:
            tasks_2a.append(run_and_bind_decision(policy_agent))
        if memory_agent:
            tasks_2a.append(run_and_bind_decision(memory_agent))
        if tasks_2a:
            await asyncio.gather(*tasks_2a)

        # Step 2b: Run Risk and Missing Info agents in parallel
        tasks_2b = []
        if risk_agent:
            tasks_2b.append(run_and_bind_decision(risk_agent))
        if missing_agent:
            tasks_2b.append(run_and_bind_decision(missing_agent))
        if tasks_2b:
            await asyncio.gather(*tasks_2b)

        # Step 2c: Run Reasoning Agent
        if reasoning_agent:
            await run_and_bind_decision(reasoning_agent)

        # Step 2d: Run Recommendation & Explainability Agent
        if rec_explain_agent:
            await run_and_bind_decision(rec_explain_agent)

        return state

    async def run(self, context: Dict[str, Any], *args, **kwargs) -> ProcurementDecisionState:
        session_id = context.get("session_id", "session_default")
        multi_vendors = context.get("multi_vendors")
        requirements = context.get("requirements") or {}
        rejected_vendors = context.get("rejected_vendors", [])
        
        # If it's a legacy single vendor call, run the standard logic:
        if not multi_vendors:
            return await self._run_single_vendor(context, *args, **kwargs)
            
        # Multi-vendor logic
        # 1. Run single-vendor pipeline for each vendor in parallel (using cached data if available)
        vendors_raw_data = context.get("vendors_raw_data") or {}
        vendors_evaluated_states = context.get("vendors_data") or {}
        
        vendor_names = list(multi_vendors)
        tasks = []
        for name in vendor_names:
            if name in vendors_evaluated_states:
                continue
                
            # Prepare context copy for this vendor
            v_raw = vendors_raw_data.get(name) or {}
            v_context = {
                "session_id": f"{session_id}_{name}",
                "vendor_name": name,
                "uploaded_files": v_raw.get("uploaded_files", []),
                "email_content": v_raw.get("email_content", ""),
                "quote_content": v_raw.get("quote_content", ""),
                "contract_content": v_raw.get("contract_content", ""),
                "meeting_content": v_raw.get("meeting_content", ""),
                "agent_timeline": []
            }
            tasks.append((name, self._run_single_vendor(v_context)))
            
        if tasks:
            names, task_objs = zip(*tasks)
            results = await asyncio.gather(*task_objs)
            for name, v_state in zip(names, results):
                vendors_evaluated_states[name] = v_state
            
        # 2. Add evaluated states to context for comparison
        context["vendors_data"] = vendors_evaluated_states
        
        # 3. Execute comparative Recommendation Agent
        rec_agent = self.decision_agents[-1] # RecommendationExplainabilityAgent is the last decision agent
        # Run sequential sleep simulation
        await asyncio.sleep(0.05)
        
        rec_result = await rec_agent.execute(context)
        if not rec_result["success"]:
            print(f"Error running comparison agent: {rec_result.get('error')}")
            from app.schemas.agent_outputs import RecommendationExplainabilityOutput
            recommendation_output = RecommendationExplainabilityOutput(
                recommendations=[],
                alternative_vendors=[],
                final_decision_tier="Tier 3 (VP & CFO)",
                human_approval_required=True
            )
        else:
            recommendation_output = rec_result["data"]
        
        # 4. Determine the currently recommended vendor name
        recommended_name = None
        if recommendation_output and recommendation_output.recommendations:
            action_text = recommendation_output.recommendations[0].action if hasattr(recommendation_output.recommendations[0], "action") else recommendation_output.recommendations[0].get("action", "")
            # Infer vendor name from action text if possible (e.g. "Approve Suresh...")
            for name in multi_vendors:
                if name.lower() in action_text.lower():
                    recommended_name = name
                    break
        
        # If we couldn't infer the name, default to the first non-rejected vendor
        if not recommended_name:
            active_list = [n for n in multi_vendors if n not in rejected_vendors]
            if active_list:
                recommended_name = active_list[0]
                
        # 5. Build consolidated state based on the recommended vendor
        main_state = None
        if recommended_name and recommended_name in vendors_evaluated_states:
            main_state = vendors_evaluated_states[recommended_name]
        else:
            # Fallback empty state
            main_state = ProcurementDecisionState(
                session_id=session_id,
                uploaded_files=[],
                agent_timeline=[]
            )
            
        # Overwrite session details for the main state
        main_state.session_id = session_id
        main_state.next_best_action = recommendation_output
        
        # 6. Build the comparison matrix for all evaluated vendors
        comparison_matrix = []
        for name in multi_vendors:
            v_state = vendors_evaluated_states.get(name)
            if not v_state:
                continue
                
            v_price = v_state.quote_data.total_amount if (v_state.quote_data and v_state.quote_data.total_amount is not None) else 0.0
            v_comp = v_state.policy_checks.compliance_status if v_state.policy_checks else "Unknown"
            v_risk = v_state.risk_assessment.risk_level if v_state.risk_assessment else "Unknown"
            v_risk_score = v_state.risk_assessment.overall_risk if v_state.risk_assessment else 0.0
            v_perf = v_state.memory_data.vendor_performance_score if v_state.memory_data else 4.0
            v_timeline = v_state.quote_data.delivery_timeline if v_state.quote_data else "Unknown"
            
            # Determine status
            status = "Recommended" if name == recommended_name else ("Rejected" if name in rejected_vendors else "Alternative")
            
            comparison_matrix.append({
                "vendor": name,
                "price": v_price,
                "compliance": v_comp,
                "risk": v_risk,
                "risk_score": v_risk_score,
                "performance": v_perf,
                "lead_time": v_timeline,
                "status": status
            })
            
        main_state.requirements = requirements
        main_state.comparison_matrix = comparison_matrix
        main_state.rejected_vendors = rejected_vendors
        main_state.recommended_vendor_name = recommended_name
        main_state.evaluated_vendors = {name: v_state.model_dump() if hasattr(v_state, "model_dump") else v_state for name, v_state in vendors_evaluated_states.items()}
        
        # 7. Merge agent timelines to show consolidated execution
        consolidated_timeline = []
        for name in multi_vendors:
            v_state = vendors_evaluated_states[name]
            for state_row in v_state.agent_timeline:
                prefixed_name = f"{name}: {state_row.agent_name}"
                consolidated_timeline.append(AgentExecutionState(
                    agent_name=prefixed_name,
                    status=state_row.status,
                    duration_ms=state_row.duration_ms,
                    error_message=state_row.error_message
                ))
                
        consolidated_timeline.append(AgentExecutionState(
            agent_name="Multi-Vendor Recommendation Agent",
            status=AgentStatusEnum.COMPLETED,
            duration_ms=300
        ))
        main_state.agent_timeline = consolidated_timeline
        
        return main_state

    async def _run_and_bind(self, agent: BaseAgent, context: Dict[str, Any], doc_type: str, state: ProcurementDecisionState):
        await asyncio.sleep(0.05)
        exec_result = await agent.execute(context)
        if exec_result["success"]:
            val = exec_result["data"]
            if doc_type == "email":
                state.email_data = val
                context["email_data"] = val
            elif doc_type == "quotation":
                state.quote_data = val
                context["quote_data"] = val
            elif doc_type == "contract":
                state.contract_data = val
                context["contract_data"] = val
            elif doc_type == "meeting_notes":
                state.meeting_data = val
                context["meeting_data"] = val
        else:
            print(f"Error executing agent {agent.name}: {exec_result.get('error')}")
