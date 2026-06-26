from app.agents.base import BaseAgent
from app.schemas.agent_outputs import NextBestActionOutput
from typing import Dict, Any

class ActionAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Action Agent",
            description="Recommends optimal procurement decisions with associated confidence scores and structured evidence."
        )

    async def run(self, context: Dict[str, Any], *args, **kwargs) -> NextBestActionOutput:
        # Placeholder for LLM Action Prompt
        return NextBestActionOutput(
            recommendation="Request CFO sign-off for Net 45 terms, waiver InfoSec review, and sign contract before end of Q3 to waive onboarding support fees ($5,000 savings).",
            reason="Signing before Q3 saves $5,000. Price is 2% below historical average, which justifies proceeding despite Net 45 term discrepancy.",
            evidence={
                "price_justification": {
                    "source": "Quotation & Memory Agent",
                    "fact": "Unit price of $1,200 is lower than previous $1,225."
                },
                "policy_deviation": {
                    "source": "Contract & RAG Agent",
                    "fact": "Contract terms are Net 45 but corporate standard requires Net 30."
                },
                "savings_opportunity": {
                    "source": "Meeting Agent",
                    "fact": "Onboarding fee of $5,000 is waived if signed by Q3 end."
                }
            },
            confidence=92.5
        )
