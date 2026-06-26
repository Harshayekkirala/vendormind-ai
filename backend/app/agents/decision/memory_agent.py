from app.agents.base import BaseAgent
from app.schemas.agent_outputs import MemoryAgentOutput
from typing import Dict, Any

class MemoryAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Memory Agent",
            description="Recalls past purchase histories, vendor delivery stats, and manager feedback."
        )

    async def run(self, context: Dict[str, Any], *args, **kwargs) -> MemoryAgentOutput:
        # Placeholder for database memory lookup (SQLite/MongoDB)
        return MemoryAgentOutput(
            previous_purchases=[
                {"purchase_id": "PO-2025-081", "date": "2025-05-12", "amount": 98000.00, "qty": 80, "unit_price": 1225.00, "status": "Delivered (3 days late)"},
                {"purchase_id": "PO-2024-114", "date": "2024-11-01", "amount": 61250.00, "qty": 50, "unit_price": 1225.00, "status": "Delivered (On time)"}
            ],
            vendor_history_summary="Overall reliable delivery rate (91%). Average rating 4.2/5. Pricing has remained stable at $1,225 per unit for past orders.",
            past_recommendations=[
                "PO-2025-081: Recommended asking for a volume discount because qty was > 50 units. (Approved by manager)"
            ],
            manager_feedback=[
                "Manager commented on PO-2025-081: 'Good catch on the volume discount, we secured Net 45 terms on that basis.'"
            ]
        )
