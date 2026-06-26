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
        # Business logic checks
        # E.g. Check if current price is higher than average historical price, check delay history, etc.
        return RiskAgentOutput(
            risk_level="Medium",
            risk_score=42.5,
            risk_factors=[
                "Payment terms in contract (Net 45) deviate from standard policy guidelines (Net 30).",
                "Vendor's delivery constraints mentioned in meeting notes show a potential 2-week onboarding delay.",
                "Quote price per unit is $1,200.00, which is slightly below the previous purchase price of $1,225.00 (Positive/Low Risk)."
            ]
        )
