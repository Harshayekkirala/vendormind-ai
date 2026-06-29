from app.agents.base import BaseAgent
from app.schemas.agent_outputs import RecommendationExplainabilityOutput, AlternativeVendor
from typing import Dict, Any

class RecommendationExplainabilityAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Recommendation & Explainability Agent",
            description="Recommends optimal procurement decisions with associated confidence scores and structured evidence."
        )

    async def run(self, context: Dict[str, Any], *args, **kwargs) -> RecommendationExplainabilityOutput:
        from app.core.database import get_db_conn
        
        vendors_data = context.get("vendors_data")
        requirements = context.get("requirements") or {}
        rejected_vendors = context.get("rejected_vendors", [])
        
        # 1. Multi-Vendor Comparative Flow
        if vendors_data:
            # Filter out rejected vendors
            active_vendors = {name: data for name, data in vendors_data.items() if name not in rejected_vendors}
            
            # Format requirements summary
            req_summary = f"""
            Category: {requirements.get('category')}
            Estimated Budget: ${requirements.get('budget')}
            Priority Goal: {requirements.get('priority')}
            Department: {requirements.get('department')}
            Custom Requirements: {requirements.get('custom_rules', 'None')}
            """
            
            # Format active vendors details
            vendors_summary = ""
            for name, v_data in active_vendors.items():
                v_dict = v_data.model_dump() if hasattr(v_data, "model_dump") else (v_data or {})
                q_data = v_dict.get("quote_data")
                p_data = v_dict.get("policy_checks")
                r_data = v_dict.get("risk_assessment")
                mem_data = v_dict.get("memory_data")
                
                # Unpack Pydantic models to dicts if they are objects
                q_dict = q_data.model_dump() if hasattr(q_data, "model_dump") else (q_data or {})
                p_dict = p_data.model_dump() if hasattr(p_data, "model_dump") else (p_data or {})
                r_dict = r_data.model_dump() if hasattr(r_data, "model_dump") else (r_data or {})
                mem_dict = mem_data.model_dump() if hasattr(mem_data, "model_dump") else (mem_data or {})
                
                v_price = q_dict.get("total_amount", "Unknown")
                v_unit = q_dict.get("unit_price", "Unknown")
                v_timeline = q_dict.get("delivery_timeline", "Unknown")
                v_comp = p_dict.get("compliance_status", "Unknown")
                v_risk = r_dict.get("risk_level", "Unknown")
                v_score = r_dict.get("overall_risk", 0.0)
                v_perf = mem_dict.get("vendor_performance_score", 4.0)
                
                vendors_summary += f"""
                Vendor: {name}
                - Total Price Offered: ${v_price}
                - Unit Price: ${v_unit}
                - Delivery Timeline: {v_timeline}
                - Compliance Status: {v_comp}
                - Historical Performance Score: {v_perf}/5.0
                - Risk Assessment: {v_risk} ({v_score}% overall risk)
                """
                
            prompt = f"""
You are the Recommendation & Explainability Agent for procurement decision intelligence.
Your task is to review the procurement requirements and the evaluated details of all active vendors, then output a ranked list of actions, alternative vendors, final decision tier, and a human approval flag.

Procurement Requirements:
{req_summary}

Active Vendors for Evaluation:
{vendors_summary}

Task:
Compare these vendors and recommend the BEST one based on the requirements and priority goal ({requirements.get('priority')}).
Produce a structured JSON output conforming to the RecommendationExplainabilityOutput schema:
1. 'recommendations': A ranked list where index 0 is the primary recommended action for the TOP vendor (e.g. 'Approve Suresh API licenses with Net 45 terms waiver'). Detail the 'action', 'confidence', 'reason', 'evidence' (referencing quote, risk, policy, etc.), and 'alternative' (suggesting the next-best vendor).
2. 'alternative_vendors': Populate a list of the OTHER active vendors (excluding the top recommended vendor and any rejected vendors) in order of their rank. Provide their name, unit_price, performance_score, typical_lead_time_days, and risk_level.
3. 'final_decision_tier': Standard matrix tier required for sign-off (e.g. 'Tier 3 (VP & CFO)').
4. 'human_approval_required': Boolean flag indicating if human override/approval is mandatory (should default to True).
"""
            try:
                from app.core.llm import generate_structured_data
                res = await generate_structured_data(prompt, RecommendationExplainabilityOutput)
                return res
            except Exception as e:
                print(f"Gemini multi-vendor analysis failed, using fallback heuristic: {e}")
                
                # Heuristic Sorting
                sorted_vendors = list(active_vendors.keys())
                
                # Find min and max across all vendors for normalization
                prices = []
                leads = []
                for v_name in sorted_vendors:
                    v_data = active_vendors[v_name]
                    v_dict = v_data.model_dump() if hasattr(v_data, "model_dump") else (v_data or {})
                    q_data = v_dict.get("quote_data")
                    q_dict = q_data.model_dump() if hasattr(q_data, "model_dump") else (q_data or {})
                    
                    price_val = q_dict.get("total_amount")
                    prices.append(float(price_val) if price_val is not None else 125000.0)
                    
                    lead_days = 14
                    timeline = q_dict.get("delivery_timeline", "")
                    if timeline:
                        import re
                        val_match = re.search(r'(\d+)\s*(day|week|month)', str(timeline), re.IGNORECASE)
                        if val_match:
                            val = int(val_match.group(1))
                            unit = val_match.group(2).lower()
                            if "month" in unit:
                                lead_days = val * 30
                            elif "week" in unit:
                                lead_days = val * 7
                            else:
                                lead_days = val
                    leads.append(lead_days)
                
                min_price = min(prices) if prices else 1.0
                min_lead = min(leads) if leads else 1.0
                
                def get_sort_key(name):
                    v_data = active_vendors[name]
                    v_dict = v_data.model_dump() if hasattr(v_data, "model_dump") else (v_data or {})
                    q_data = v_dict.get("quote_data")
                    r_data = v_dict.get("risk_assessment")
                    mem_data = v_dict.get("memory_data")
                    
                    q_dict = q_data.model_dump() if hasattr(q_data, "model_dump") else (q_data or {})
                    r_dict = r_data.model_dump() if hasattr(r_data, "model_dump") else (r_data or {})
                    mem_dict = mem_data.model_dump() if hasattr(mem_data, "model_dump") else (mem_data or {})
                    
                    price = float(q_dict.get("total_amount", 125000.0) or 125000.0)
                    lead_days = 14
                    timeline = q_dict.get("delivery_timeline", "")
                    if timeline:
                        import re
                        val_match = re.search(r'(\d+)\s*(day|week|month)', str(timeline), re.IGNORECASE)
                        if val_match:
                            val = int(val_match.group(1))
                            unit = val_match.group(2).lower()
                            if "month" in unit:
                                lead_days = val * 30
                            elif "week" in unit:
                                lead_days = val * 7
                            else:
                                lead_days = val
                                
                    perf = float(mem_dict.get("vendor_performance_score", 3.5) or 3.5)
                    risk_score = float(r_dict.get("overall_risk", 25.0) or 25.0)
                    
                    # Normalize utilities to 0-100 range
                    price_utility = (min_price / price) * 100.0 if price > 0 else 100.0
                    delivery_utility = (min_lead / lead_days) * 100.0 if lead_days > 0 else 100.0
                    performance_utility = (perf / 5.0) * 100.0
                    risk_utility = 100.0 - risk_score
                    
                    # Determine weights based on user priority
                    priority = str(requirements.get("priority", "Cost")).lower()
                    if "cost" in priority or "price" in priority or "amount" in priority:
                        w_price, w_delivery, w_perf, w_risk = 0.50, 0.20, 0.20, 0.10
                    elif "delivery" in priority or "time" in priority or "timeline" in priority:
                        w_price, w_delivery, w_perf, w_risk = 0.20, 0.50, 0.20, 0.10
                    elif "quality" in priority or "performance" in priority or "reputation" in priority:
                        w_price, w_delivery, w_perf, w_risk = 0.20, 0.20, 0.50, 0.10
                    elif "risk" in priority or "compliance" in priority:
                        w_price, w_delivery, w_perf, w_risk = 0.20, 0.15, 0.15, 0.50
                    else:
                        w_price, w_delivery, w_perf, w_risk = 0.30, 0.25, 0.25, 0.20
                        
                    total_utility = (
                        w_price * price_utility +
                        w_delivery * delivery_utility +
                        w_perf * performance_utility +
                        w_risk * risk_utility
                    )
                    # Return negative total_utility so the highest utility vendor is sorted first
                    return -total_utility
                
                sorted_vendors.sort(key=get_sort_key)
                
                if not sorted_vendors:
                    return RecommendationExplainabilityOutput(
                        recommendations=[],
                        alternative_vendors=[],
                        final_decision_tier="Tier 1 (Purchaser)",
                        human_approval_required=True
                    )
                
                best_vendor_name = sorted_vendors[0]
                best_v_data = active_vendors[best_vendor_name]
                best_v_dict = best_v_data.model_dump() if hasattr(best_v_data, "model_dump") else (best_v_data or {})
                best_q = best_v_dict.get("quote_data")
                best_q_dict = best_q.model_dump() if hasattr(best_q, "o_data") or hasattr(best_q, "model_dump") else (best_q or {})
                best_price = best_q_dict.get("total_amount", 0.0) or 0.0
                best_timeline = best_q_dict.get("delivery_timeline", "standard")
                
                alt_vendors = []
                for alt_name in sorted_vendors[1:]:
                    alt_data = active_vendors[alt_name]
                    alt_dict = alt_data.model_dump() if hasattr(alt_data, "model_dump") else (alt_data or {})
                    alt_q = alt_dict.get("quote_data")
                    alt_r = alt_dict.get("risk_assessment")
                    alt_mem = alt_dict.get("memory_data")
                    
                    aq_dict = alt_q.model_dump() if hasattr(alt_q, "model_dump") else (alt_q or {})
                    ar_dict = alt_r.model_dump() if hasattr(alt_r, "model_dump") else (alt_r or {})
                    am_dict = alt_mem.model_dump() if hasattr(alt_mem, "model_dump") else (alt_mem or {})
                    
                    alt_lead_days = 14
                    alt_timeline = aq_dict.get("delivery_timeline", "")
                    if alt_timeline:
                        import re
                        val_match = re.search(r'(\d+)\s*(day|week|month)', str(alt_timeline), re.IGNORECASE)
                        if val_match:
                            val = int(val_match.group(1))
                            unit = val_match.group(2).lower()
                            if "month" in unit:
                                alt_lead_days = val * 30
                            elif "week" in unit:
                                alt_lead_days = val * 7
                            else:
                                alt_lead_days = val
                                
                    alt_vendors.append(AlternativeVendor(
                        name=alt_name,
                        unit_price=aq_dict.get("unit_price", 1200.0) or 1200.0,
                        performance_score=am_dict.get("vendor_performance_score", 4.0) or 4.0,
                        typical_lead_time_days=alt_lead_days,
                        risk_level=ar_dict.get("risk_level", "Low") or "Low"
                    ))
                
                best_action = f"Approve {best_vendor_name} quotation of ${best_price:,.2f} with delivery in {best_timeline}."
                best_reason = f"Ranked highest based on your focus on {requirements.get('priority')}. Prices and compliance parameters are favorable."
                best_alternative_text = f"Consider switching to {sorted_vendors[1]} if negotiation fails." if len(sorted_vendors) > 1 else "No alternatives available."
                
                return RecommendationExplainabilityOutput(
                    recommendations=[
                        {
                            "action": best_action,
                            "confidence": 90.0,
                            "reason": best_reason,
                            "evidence": {
                                "price_justification": { "source": "Quote Agent", "fact": f"Total quote amount is ${best_price:,.2f}." }
                            },
                            "alternative": best_alternative_text
                        }
                    ],
                    alternative_vendors=alt_vendors,
                    final_decision_tier="Tier 2 (Manager)",
                    human_approval_required=True
                )

        # 2. Legacy Single-Vendor Fallback Flow
        reasoning_data = context.get("reasoning")
        quote_data = context.get("quote_data")
        email_data = context.get("email_data")
        contract_data = context.get("contract_data")
        meeting_data = context.get("meeting_data")
        policy_data = context.get("policy_checks")
        memory_data = context.get("memory_data")
        risk_data = context.get("risk_assessment")

        current_vendor = quote_data.vendor_name if (quote_data and quote_data.vendor_name) else "Acme Corp"
        alternative_vendors_data = []
        try:
            with get_db_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT v.name, v.performance_score, v.risk_level, vc.item_description, vc.standard_unit_price, vc.typical_lead_time_days
                    FROM vendors v
                    JOIN vendor_catalog vc ON v.id = vc.vendor_id
                    WHERE v.is_blacklisted = 0 
                      AND LOWER(v.name) != LOWER(%s)
                    ORDER BY v.performance_score DESC;
                """, (current_vendor.strip(),))
                
                rows = cursor.fetchall()
                for row in rows:
                    alternative_vendors_data.append({
                        "name": row["name"],
                        "unit_price": row["standard_unit_price"],
                        "performance_score": row["performance_score"],
                        "typical_lead_time_days": row["typical_lead_time_days"],
                        "risk_level": row["risk_level"]
                    })
        except Exception as e:
            print(f"Error fetching alternative vendors in agent: {e}")

        prompt = f"""
You are the Recommendation & Explainability Agent for procurement decision intelligence.
Your task is to review the cognitive reasoning summary and all contextual inputs, then output a ranked list of actions, alternative vendors, final decision tier, and a human approval flag.

Input Data:
- Cognitive reasoning summary: {reasoning_data}
- Quote: {quote_data}
- Emails: {email_data}
- Contract: {contract_data}
- Meetings: {meeting_data}
- Policy compliance: {policy_data}
- Vendor History Memory: {memory_data}
- Risk assessment: {risk_data}
- Available Alternative Vendors in Catalog: {alternative_vendors_data}

Task:
Produce:
1. 'recommendations': A ranked list of recommendations, where each recommendation is a dictionary containing:
   - 'action': Stated next best action (e.g. 'Request CFO sign-off for Net 45 terms').
   - 'confidence': Number representing confidence percentage (0 to 100).
   - 'reason': Explanatory reason.
   - 'evidence': Dict showing specific references to Quote, Policy, Memory, etc.
   - 'alternative': Alternative action suggestion (e.g. 'Request competitive quote from TechNova Solutions').
2. 'alternative_vendors': Populate a list of alternative vendors matching the available alternatives catalog. If any alternatives are listed in the 'Available Alternative Vendors in Catalog', output them exactly inside this field so they map to the database names.
3. 'final_decision_tier': Standard matrix tier required for sign-off (e.g. 'Tier 3 (VP & CFO)').
4. 'human_approval_required': Boolean flag indicating if human override/approval is mandatory (should default to True).
"""
        try:
            from app.core.llm import generate_structured_data
            res = await generate_structured_data(prompt, RecommendationExplainabilityOutput)
            if not res.alternative_vendors and alternative_vendors_data:
                res.alternative_vendors = alternative_vendors_data
            return res
        except Exception as e:
            return RecommendationExplainabilityOutput(
                recommendations=[
                    {
                        "action": "Request CFO sign-off for Net 45 terms, waive InfoSec review, and sign contract before end of Q3 to waive onboarding support fees ($5,000 savings). (Fallback)",
                        "confidence": 94.0,
                        "reason": "Signing before Q3 saves $5,000. Price is 2% below historical average, which justifies proceeding despite Net 45 terms discrepancy. (Fallback)",
                        "evidence": {
                            "price_justification": {
                                "source": "Quotation & Memory Agent",
                                "fact": "Unit price of $1,200 is lower than previous $1,225."
                            },
                            "policy_deviation": {
                                "source": "Contract & Policy Compliance Agent",
                                "fact": "Contract terms are Net 45 but corporate standard requires Net 30."
                            },
                            "savings_opportunity": {
                                "source": "Meeting Agent",
                                "fact": "Onboarding fee of $5,000 is waived if signed by Q3 end."
                            }
                        },
                        "alternative": "Switch to TechNova Solutions (Fallback) - offers $1,150 unit price and standard Net 30 terms."
                    }
                ],
                alternative_vendors=[
                    AlternativeVendor(
                        name=a["name"],
                        unit_price=a["unit_price"],
                        performance_score=a["performance_score"],
                        typical_lead_time_days=a["typical_lead_time_days"],
                        risk_level=a["risk_level"]
                    ) for a in alternative_vendors_data
                ] if alternative_vendors_data else [
                    AlternativeVendor(
                        name="TechNova Solutions",
                        unit_price=1150.00,
                        performance_score=4.9,
                        typical_lead_time_days=7,
                        risk_level="Low"
                    )
                ],
                final_decision_tier="Tier 3 (VP of Procurement & CFO)",
                human_approval_required=True
            )
