from app.agents.base import BaseAgent
from app.schemas.agent_outputs import RiskAgentOutput
from typing import Dict, Any

class RiskAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Risk Agent",
            description="Performs risk modeling based on delivery histories, pricing variances, and legal clauses."
        )

    async def run(self, context: Dict[str, Any], *args, **kwargs) -> RiskAgentOutput:
        quote_data = context.get("quote_data")
        email_data = context.get("email_data")
        contract_data = context.get("contract_data")
        meeting_data = context.get("meeting_data")
        policy_data = context.get("policy_checks")
        memory_data = context.get("memory_data")

        prompt = f"""
You are an expert enterprise procurement Risk Assessment Agent.
Your task is to compute risk percentage metrics across multiple risk dimensions.

Input Context:
- Quotation: {quote_data}
- Email negotiations: {email_data}
- Contract clauses: {contract_data}
- Meeting transcripts: {meeting_data}
- Policy Check compliance: {policy_data}
- Vendor History: {memory_data}

Task:
Evaluate and return:
1. 'overall_risk': Weighted overall risk score (0 to 100%).
2. 'delivery_risk': Risk of shipping delays or supply chain blockers (0 to 100%).
3. 'financial_risk': Overpayment, price anomaly, or tax/GST compliance risk (0 to 100%).
4. 'legal_risk': High-risk clauses, missing penalty terms, or liability limits (0 to 100%).
5. 'operational_risk': InfoSec reviews, SOAP/API endpoints integrations risk (0 to 100%).
6. 'vendor_risk': Default risk based on historical vendor scores and late rates (0 to 100%).
7. 'compliance_risk': Violations of company standards, approval matrix deviations (0 to 100%).
8. 'risk_level': 'Low', 'Medium', or 'High'.
9. 'risk_factors': List of descriptions explaining the risk scores.
"""
        try:
            from app.core.llm import generate_structured_data
            return await generate_structured_data(prompt, RiskAgentOutput)
        except Exception as e:
            # Fallback to dynamic compliance-based mock risk data matching schema
            overall = 25.0
            factors = []
            if policy_data:
                if policy_data.purchase_limit_exceeded:
                    overall += 15.0
                    factors.append("Purchase limit exceeded policy thresholds. (Fallback)")
                if policy_data.vendor_blacklisted:
                    overall += 50.0
                    factors.append("Vendor is flagged in blacklist lookup. (Fallback)")
                if policy_data.missing_required_documents:
                    overall += 10.0 * len(policy_data.missing_required_documents)
                    factors.append(f"Missing required documents: {', '.join(policy_data.missing_required_documents)}. (Fallback)")
            
            if not factors:
                factors.append("No critical compliance deviations flagged. (Fallback)")
                
            overall = min(overall, 100.0)
            level = "Low" if overall < 30 else ("Medium" if overall < 60 else "High")
            
            return RiskAgentOutput(
                overall_risk=overall,
                delivery_risk=overall * 0.2,
                financial_risk=overall * 0.4,
                legal_risk=overall * 0.3,
                operational_risk=overall * 0.3,
                vendor_risk=overall * 0.2,
                compliance_risk=overall * 0.5,
                risk_level=level,
                risk_factors=factors
            )
