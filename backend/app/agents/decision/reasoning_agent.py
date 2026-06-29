from app.agents.base import BaseAgent
from app.schemas.agent_outputs import ReasoningAgentOutput
from typing import Dict, Any

class ReasoningAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Reasoning Agent",
            description="Synthesizes extraction results, RAG reviews, memory performance, and risk assessments into a business situation summary."
        )

    async def run(self, context: Dict[str, Any], *args, **kwargs) -> ReasoningAgentOutput:
        quote_data = context.get("quote_data")
        email_data = context.get("email_data")
        contract_data = context.get("contract_data")
        meeting_data = context.get("meeting_data")
        policy_data = context.get("policy_checks")
        memory_data = context.get("memory_data")
        risk_data = context.get("risk_assessment")
        missing_data = context.get("missing_info")

        prompt = f"""
You are the core procurement Decision Reasoning Agent.
Your task is to analyze all data inputs from previous specialized agents and compile a comprehensive cognitive summary of the business situation, explaining the pros, cons, and potential guideline checks.

Deal Details:
- Quote details: {quote_data}
- Email commitments: {email_data}
- Contract terms: {contract_data}
- Meeting decisions: {meeting_data}

Compliance & Context checks:
- Policy compliance RAG: {policy_data}
- Historic vendor memory: {memory_data}
- Identified Risk factors: {risk_data}
- Gaps / Missing Information: {missing_data}

Task:
Produce and return:
1. 'situation_summary': A comprehensive situation summary explaining the transaction context and any compliance/business anomalies.
2. 'cognitive_findings': A list of key findings, where each finding is a dictionary containing:
   - 'fact': The specific extracted fact or guideline value.
   - 'source': The source agent or document (e.g. 'Quote Agent', 'Policy Compliance Agent').
   - 'reasoning_step': Explanation of how this fact impacts the final reasoning.
"""
        try:
            from app.core.llm import generate_structured_data
            return await generate_structured_data(prompt, ReasoningAgentOutput)
        except Exception as e:
            # Fallback to realistic dynamic mock reasoning data matching schema
            vendor = quote_data.vendor_name if quote_data and quote_data.vendor_name else "the vendor"
            price = quote_data.total_amount if quote_data and quote_data.total_amount else 0.0
            
            summary = f"The team is analyzing the procurement quote from {vendor} for a total of ${price:,.2f}."
            if policy_data:
                summary += f" Compliance review indicates status as {policy_data.compliance_status}."
                if policy_data.purchase_limit_exceeded:
                    summary += " The purchase amount exceeds the standard $100k buyer threshold."
            summary += " (Fallback)"
            
            return ReasoningAgentOutput(
                situation_summary=summary,
                cognitive_findings=[
                    {
                        "fact": f"Quoted total is ${price:,.2f}.",
                        "source": "Quote Agent",
                        "reasoning_step": f"Used for transaction threshold verification for {vendor}. (Fallback)"
                    },
                    {
                        "fact": f"Compliance status is {policy_data.compliance_status if policy_data else 'Conditional'}.",
                        "source": "Policy Compliance Agent",
                        "reasoning_step": f"Controls final sign-off escalation routing. (Fallback)"
                    }
                ]
            )
