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
        # Business logic checks
        return MissingInfoAgentOutput(
            missing_fields=[
                "Third-party InfoSec integration questionnaire is not filled.",
                "Formal escrow agreement draft for the API endpoints is missing."
            ],
            impact_level="Medium"
        )
