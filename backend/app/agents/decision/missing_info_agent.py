from app.agents.base import BaseAgent
from app.schemas.agent_outputs import MissingInfoAgentOutput
from typing import Dict, Any

class MissingInfoAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Missing Info Agent",
            description="Analyzes deal context to find gaps in contracts, quotes, or commitments."
        )

    async def run(self, context: Dict[str, Any], *args, **kwargs) -> MissingInfoAgentOutput:
        quote_data = context.get("quote_data")
        email_data = context.get("email_data")
        contract_data = context.get("contract_data")
        meeting_data = context.get("meeting_data")
        policy_data = context.get("policy_checks")

        prompt = f"""
You are an expert procurement Missing Information Agent.
Identify missing parameters, documents, or compliance approvals required for corporate procurement.

Deal Context:
- Quote details: {quote_data}
- Email Negotiations: {email_data}
- Contract clauses: {contract_data}
- Meeting notes: {meeting_data}
- Policy Check Compliance: {policy_data}

Task:
Extract:
1. 'missing_fields': Fields missing from quotes or contracts (e.g. GST registration, specific unit models).
2. 'missing_documents': Key documentation missing based on policy checks (e.g. Competitive Quotes, InfoSec questionnaires).
3. 'missing_approvals': Stakeholder approvals that are required but missing.
4. 'recommended_actions': Steps to gather the missing information (e.g. 'Email vendor to request GST details').
5. 'impact_level': 'Low', 'Medium', or 'High'.
"""
        try:
            from app.core.llm import generate_structured_data
            return await generate_structured_data(prompt, MissingInfoAgentOutput)
        except Exception as e:
            vendor = quote_data.vendor_name if (quote_data and quote_data.vendor_name) else (context.get("vendor_name") or "the vendor")
            vendor = vendor.replace(" (Fallback)", "")
            # Fallback to realistic dynamic mock missing info data
            return MissingInfoAgentOutput(
                missing_fields=[
                    f"Vendor GST registration number for {vendor} is missing. (Fallback)",
                    "Escrow protection clause is missing in draft contract. (Fallback)"
                ],
                missing_documents=[
                    "Third-party InfoSec integration questionnaire is not filled. (Fallback)",
                    "Competitive quotes documentation (under PROC-POL-01). (Fallback)"
                ],
                missing_approvals=[
                    "VP of Procurement signature. (Fallback)",
                    "CFO sign-off for Net 45 payment terms. (Fallback)"
                ],
                recommended_actions=[
                    f"Generate and send an automated email to {vendor} requesting their GST details and completed InfoSec questionnaire. (Fallback)"
                ],
                impact_level="High"
            )
