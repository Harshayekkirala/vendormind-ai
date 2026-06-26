from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

# ==========================================
# 📊 EXTRACTION AGENTS OUTPUTS (Dev 1)
# ==========================================

class EmailAgentOutput(BaseModel):
    delivery: Optional[str] = Field(None, description="Delivery timelines promised in the email")
    discount: Optional[str] = Field(None, description="Discounts offered or negotiated")
    commitments: List[str] = Field(default_factory=list, description="List of key commitments made by the sender")
    vendor_promises: List[str] = Field(default_factory=list, description="Vendor promises or assurances")

class QuoteAgentOutput(BaseModel):
    price: Optional[float] = Field(None, description="Total quoted price")
    currency: str = Field(default="USD", description="Currency of quoted price")
    quantity: Optional[int] = Field(None, description="Total quantity of items")
    items: List[Dict[str, Any]] = Field(default_factory=list, description="List of items with price and description")
    warranty: Optional[str] = Field(None, description="Warranty details mentioned in the quote")
    delivery: Optional[str] = Field(None, description="Delivery details/timeline from the quote")

class ContractAgentOutput(BaseModel):
    payment_terms: Optional[str] = Field(None, description="Payment terms (e.g., Net 30)")
    penalty_clause: Optional[str] = Field(None, description="Penalty clauses for delays/defaults")
    sla: Optional[str] = Field(None, description="Service Level Agreements mentioned")
    warranty: Optional[str] = Field(None, description="Warranty details from the contract")

class MeetingAgentOutput(BaseModel):
    agreements: List[str] = Field(default_factory=list, description="Agreements reached during the meeting")
    risks: List[str] = Field(default_factory=list, description="Risks raised during the discussion")
    action_items: List[str] = Field(default_factory=list, description="Assigned action items")
    deliverables: List[str] = Field(default_factory=list, description="Expected deliverables")


# ==========================================
# 🧠 DECISION AGENTS OUTPUTS (Dev 2)
# ==========================================

class RAGAgentOutput(BaseModel):
    relevant_policies: List[str] = Field(default_factory=list, description="Matched corporate procurement policies")
    sop_guidelines: List[str] = Field(default_factory=list, description="SOP steps applicable to this purchase")
    approval_matrix: Dict[str, Any] = Field(default_factory=dict, description="Required approval authority levels")

class MemoryAgentOutput(BaseModel):
    previous_purchases: List[Dict[str, Any]] = Field(default_factory=list, description="Previous orders from this vendor")
    vendor_history_summary: Optional[str] = Field(None, description="Performance review summary of this vendor")
    past_recommendations: List[str] = Field(default_factory=list, description="Actions recommended in the past")
    manager_feedback: List[str] = Field(default_factory=list, description="Previous manager overrides or comments")

class RiskAgentOutput(BaseModel):
    risk_level: str = Field(..., description="Low, Medium, or High risk assessment")
    risk_score: float = Field(..., description="Numerical risk score percentage (0-100%)")
    risk_factors: List[str] = Field(default_factory=list, description="Factors contributing to the risk score")

class MissingInfoAgentOutput(BaseModel):
    missing_fields: List[str] = Field(default_factory=list, description="Important details (e.g. warranty, delivery dates) that are missing")
    impact_level: str = Field(default="Low", description="Impact level of missing information (Low, Medium, High)")

class ReasoningAgentOutput(BaseModel):
    situation_summary: str = Field(..., description="Comprehensive summary of the business scenario")
    key_findings: List[str] = Field(default_factory=list, description="Key insights synthesized from all documents")

class NextBestActionOutput(BaseModel):
    recommendation: str = Field(..., description="Action recommendation (e.g. 'Negotiate Price', 'Proceed with Sign-off')")
    reason: str = Field(..., description="Primary reason for the recommendation")
    evidence: Dict[str, Any] = Field(default_factory=dict, description="Evidence references mapping to emails, quotes, policies")
    confidence: float = Field(..., description="Confidence score percentage (0-100%)")


# ==========================================
# 🏁 CONSOLIDATED PLATFORM STATE
# ==========================================

class AgentStatusEnum(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"

class AgentExecutionState(BaseModel):
    agent_name: str
    status: AgentStatusEnum
    duration_ms: Optional[int] = None
    error_message: Optional[str] = None

class ProcurementDecisionState(BaseModel):
    session_id: str
    uploaded_files: List[str]
    agent_timeline: List[AgentExecutionState] = Field(default_factory=list)
    
    # Extracted Data
    email_data: Optional[EmailAgentOutput] = None
    quote_data: Optional[QuoteAgentOutput] = None
    contract_data: Optional[ContractAgentOutput] = None
    meeting_data: Optional[MeetingAgentOutput] = None
    
    # Decision Intelligence
    rag_checks: Optional[RAGAgentOutput] = None
    memory_data: Optional[MemoryAgentOutput] = None
    risk_assessment: Optional[RiskAgentOutput] = None
    missing_info: Optional[MissingInfoAgentOutput] = None
    reasoning: Optional[ReasoningAgentOutput] = None
    next_best_action: Optional[NextBestActionOutput] = None
