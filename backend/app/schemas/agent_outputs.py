from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

# ==========================================
# 📊 EXTRACTION AGENTS OUTPUTS (Dev 1)
# ==========================================

class EmailAgentOutput(BaseModel):
    delivery_days: Optional[int] = Field(None, description="Delivery timeline in number of days promised")
    discount_percentage: Optional[float] = Field(None, description="Discounts percentage offered or negotiated")
    urgency: str = Field(..., description="High, Medium, or Low urgency level")
    commitments: List[str] = Field(default_factory=list, description="Specific vendor commitments or assurances")
    escalation_requested: bool = Field(default=False, description="Flag indicating if sender requested escalation")
    contact_details: Optional[str] = Field(None, description="Extracted contact info of negotiator")
    negotiation_language: Optional[str] = Field(None, description="Negotiation-specific comments or requests")

class QuoteAgentOutput(BaseModel):
    total_amount: Optional[float] = Field(None, description="Total quoted price")
    tax_amount: Optional[float] = Field(None, description="Tax amount or GST details")
    currency: str = Field(default="USD", description="Currency of quoted price")
    warranty_period: Optional[str] = Field(None, description="Warranty details mentioned in the quote")
    total_quantity: Optional[int] = Field(None, description="Total quantity of items")
    unit_price: Optional[float] = Field(None, description="Calculated or stated unit price")
    delivery_timeline: Optional[str] = Field(None, description="Delivery timelines promised in the quotation")
    vendor_name: Optional[str] = Field(None, description="Vendor name stated in the quote")
    items: List[Dict[str, Any]] = Field(default_factory=list, description="Line item details")

class ContractAgentOutput(BaseModel):
    penalty_clause: Optional[str] = Field(None, description="Penalty terms for delay or non-compliance")
    warranty_terms: Optional[str] = Field(None, description="Warranty period and details")
    support_terms: Optional[str] = Field(None, description="Support terms (e.g. 24/7 SLA response times)")
    termination_clause: Optional[str] = Field(None, description="Termination and notice periods")
    sla_terms: Optional[str] = Field(None, description="Service Level Agreement metrics")
    payment_schedule: Optional[str] = Field(None, description="Payment schedule details (e.g. Net 30, Net 45)")
    confidentiality_clause: Optional[str] = Field(None, description="Confidentiality and non-disclosure details")
    liability_limit: Optional[str] = Field(None, description="Limitation of liability terms")

class MeetingAgentOutput(BaseModel):
    decisions: List[str] = Field(default_factory=list, description="Key decisions made in the meeting")
    risks: List[str] = Field(default_factory=list, description="Risks or concerns raised during meeting")
    promises: List[str] = Field(default_factory=list, description="Verbal commitments or promises made")
    action_items: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Action items (must contain 'description', 'owner', and 'deadline')"
    )
    stakeholders: List[str] = Field(default_factory=list, description="Meeting attendees or stakeholders")
    blockers: List[str] = Field(default_factory=list, description="Unresolved items or blockers")


# ==========================================
# 🧠 DECISION AGENTS OUTPUTS (Dev 2)
# ==========================================

class PolicyVerdictItem(BaseModel):
    code: str = Field(..., description="Policy code e.g. SEC-POL-01")
    category: str = Field(..., description="Policy category e.g. security, payment_terms")
    text: str = Field(..., description="Short description of the policy rule")
    status: str = Field(..., description="PASS or FAIL")
    reason: str = Field(default="", description="Why this policy passed or failed for this vendor")

class PolicyComplianceAgentOutput(BaseModel):
    purchase_limit_exceeded: bool = Field(..., description="True if amount exceeds policy limits for buyer")
    approvals_required: List[str] = Field(default_factory=list, description="Tiers or individuals needed for approval")
    vendor_blacklisted: bool = Field(..., description="True if vendor is blacklisted")
    missing_required_documents: List[str] = Field(default_factory=list, description="Documents required but not uploaded")
    compliance_status: str = Field(..., description="Compliant, Non-Compliant, or Conditional")
    policy_verdict: List[PolicyVerdictItem] = Field(default_factory=list, description="Per-policy pass/fail results")
    decision_reason: str = Field(default="", description="Human-readable summary of why vendor was recommended or rejected based on policies")

class MemoryAgentOutput(BaseModel):
    past_purchases: List[Dict[str, Any]] = Field(default_factory=list, description="List of previous transactions")
    vendor_performance_score: float = Field(..., description="Vendor historical rating or score (e.g. 0.0 to 5.0)")
    previous_contract_count: int = Field(..., description="Count of past contracts signed with this vendor")
    pending_disputes: List[str] = Field(default_factory=list, description="Open disputes or complaints with vendor")
    negotiation_history_summary: Optional[str] = Field(None, description="Summary of historic negotiations")

class RiskAgentOutput(BaseModel):
    overall_risk: float = Field(..., description="Overall risk percentage (0 to 100%)")
    delivery_risk: float = Field(..., description="Delivery delay risk (0 to 100%)")
    financial_risk: float = Field(..., description="Financial anomaly or overpayment risk (0 to 100%)")
    legal_risk: float = Field(..., description="Contract risk factor (0 to 100%)")
    operational_risk: float = Field(..., description="Operational integration risk (0 to 100%)")
    vendor_risk: float = Field(..., description="Vendor performance default risk (0 to 100%)")
    compliance_risk: float = Field(..., description="Policy violation risk (0 to 100%)")
    risk_level: str = Field(..., description="Low, Medium, or High risk assessment")
    risk_factors: List[str] = Field(default_factory=list, description="List of risk descriptions")

class MissingInfoAgentOutput(BaseModel):
    missing_fields: List[str] = Field(default_factory=list, description="Fields missing from documents (e.g. GST, Warranty)")
    missing_documents: List[str] = Field(default_factory=list, description="Missing transaction documents")
    missing_approvals: List[str] = Field(default_factory=list, description="Required approvals that are not yet uploaded")
    recommended_actions: List[str] = Field(default_factory=list, description="Steps recommended to gather this information")
    impact_level: str = Field(..., description="Low, Medium, or High impact level")

class ReasoningAgentOutput(BaseModel):
    situation_summary: str = Field(..., description="Cognitive synthesis of the entire deal")
    cognitive_findings: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Findings showing 'fact', 'source', and 'reasoning_step' for absolute explainability"
    )

class AlternativeVendor(BaseModel):
    name: str = Field(..., description="Name of the alternative vendor")
    unit_price: Optional[float] = Field(0.0, description="Standard unit price offered by the vendor")
    performance_score: Optional[float] = Field(4.0, description="Historical performance score of the vendor")
    typical_lead_time_days: Optional[int] = Field(14, description="Standard delivery lead time in days")
    risk_level: Optional[str] = Field("Low", description="Assessed risk level: Low, Medium, High")

class RecommendationExplainabilityOutput(BaseModel):
    recommendations: List[Dict[str, Any]] = Field(
        ..., 
        description="Ranked suggestions containing 'action', 'confidence', 'reason', 'evidence', and 'alternative'"
    )
    alternative_vendors: List[AlternativeVendor] = Field(
        default_factory=list,
        description="List of alternative vendors in the catalog"
    )
    final_decision_tier: str = Field(..., description="Determined approval matrix tier required")
    human_approval_required: bool = Field(default=True, description="Always true for procurement actions")


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
    policy_checks: Optional[PolicyComplianceAgentOutput] = None
    memory_data: Optional[MemoryAgentOutput] = None
    risk_assessment: Optional[RiskAgentOutput] = None
    missing_info: Optional[MissingInfoAgentOutput] = None
    reasoning: Optional[ReasoningAgentOutput] = None
    next_best_action: Optional[RecommendationExplainabilityOutput] = None

    # Multi-Vendor Comparison Extension
    requirements: Optional[Dict[str, Any]] = None
    comparison_matrix: Optional[List[Dict[str, Any]]] = None
    rejected_vendors: List[str] = Field(default_factory=list)
    recommended_vendor_name: Optional[str] = None
    evaluated_vendors: Optional[Dict[str, Any]] = None
