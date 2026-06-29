from app.agents.base import BaseAgent
from app.schemas.agent_outputs import PolicyComplianceAgentOutput, PolicyVerdictItem
from typing import Dict, Any

class PolicyComplianceAgent(BaseAgent):
    def __init__(self):
        super().__init__(
            name="Policy Compliance Agent",
            description="Performs retrieval checks against corporate guidelines, SOPs, and approval matrices."
        )

    async def run(self, context: Dict[str, Any], *args, **kwargs) -> PolicyComplianceAgentOutput:
        # Search policies in the local RAG store
        email_text = context.get("email_content", "")
        quote_text = context.get("quote_content", "")
        contract_text = context.get("contract_content", "")
        search_query = f"{email_text} {quote_text} {contract_text}"
        
        from app.core.rag_store import rag_store
        matching_policies = rag_store.search_policies(search_query)
        matrix = rag_store.get_approval_matrix()
        
        # Pull extracted data if present
        quote_data = context.get("quote_data")
        price_val = quote_data.total_amount if (quote_data and quote_data.total_amount is not None) else 0.0
        vendor_val = quote_data.vendor_name if (quote_data and quote_data.vendor_name is not None) else "Unknown Vendor"
        contract_data = context.get("contract_data")
        terms_val = contract_data.payment_schedule if (contract_data and contract_data.payment_schedule is not None) else "Unknown"
        warranty_val = contract_data.warranty_terms if (contract_data and contract_data.warranty_terms is not None) else ""
        sla_val = contract_data.sla_terms if (contract_data and contract_data.sla_terms is not None) else ""
        penalty_val = contract_data.penalty_clause if (contract_data and contract_data.penalty_clause is not None) else ""

        # Apply database RAG heuristics
        vendor_blacklisted = rag_store.is_vendor_blacklisted(vendor_val)
        purchase_limit_exceeded = rag_store.check_purchase_limit_exceeded(price_val)
        
        # Check uploaded files lists vs required documents
        uploaded_files = context.get("uploaded_files", [])
        required_docs = rag_store.get_required_documents(price_val)
        missing_docs = []
        for rd in required_docs:
            has_doc = any(rd in uf.lower() or ("quote" in rd and "quotation" in uf.lower()) for uf in uploaded_files)
            if not has_doc:
                missing_docs.append(rd)

        # Build per-policy verdict by checking each DB policy rule
        policy_verdict = []
        try:
            from app.core.database import get_db_conn
            with get_db_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT code, category, text FROM policies ORDER BY code;")
                all_policies = cursor.fetchall()
            
            for pol in all_policies:
                code = pol["code"]
                category = pol["category"]
                text = pol["text"]
                status = "PASS"
                reason = "No issues detected."

                # ── Security policies ────────────────────────────────────
                if code == "SEC-POL-01":
                    # ISO 27001 check: look for mention in contract or quote
                    if contract_text and ("iso 27001" in contract_text.lower() or "iso27001" in contract_text.lower()):
                        reason = "ISO 27001 compliance mentioned in contract documents."
                    else:
                        status = "FAIL"
                        reason = "No ISO 27001 compliance clause found in contract."

                elif code == "SEC-POL-02":
                    if contract_text and ("encrypt" in contract_text.lower() or "aes" in contract_text.lower()):
                        reason = "Data encryption terms present in contract."
                    else:
                        status = "FAIL"
                        reason = "No data encryption commitment found in contract."

                elif code == "SEC-POL-03":
                    if contract_text and ("access log" in contract_text.lower() or "audit log" in contract_text.lower()):
                        reason = "Access logging terms present in contract."
                    else:
                        status = "FAIL"
                        reason = "No access logging commitment found."

                elif code == "SEC-POL-04":
                    if contract_text and ("confidential" in contract_text.lower() or "non-disclosure" in contract_text.lower() or "nda" in contract_text.lower()):
                        reason = "Confidentiality clause present in contract."
                    else:
                        status = "FAIL"
                        reason = "No confidentiality or NDA clause found in contract."

                elif code == "SEC-POL-05":
                    if contract_text and ("mfa" in contract_text.lower() or "multi-factor" in contract_text.lower() or "two-factor" in contract_text.lower()):
                        reason = "MFA requirement referenced in contract."
                    else:
                        status = "FAIL"
                        reason = "Multi-factor authentication not referenced in contract."

                elif code == "SEC-POL-06":
                    if contract_text and ("incident" in contract_text.lower() or "breach" in contract_text.lower()):
                        reason = "Security incident reporting clause referenced in contract."
                    else:
                        status = "FAIL"
                        reason = "No security incident reporting commitment within 24 hours found."

                # ── Payment policies ─────────────────────────────────────
                elif code == "PAY-POL-01":
                    if "advance" in (email_text + contract_text + quote_text).lower():
                        if "20%" in (contract_text + quote_text):
                            reason = "Advance payment at or below 20% as per policy."
                        else:
                            status = "FAIL"
                            reason = "Advance payment terms present but percentage not verifiable; assumed over limit."
                    else:
                        reason = "No advance payment mentioned; assumes compliant."

                elif code == "PAY-POL-02":
                    if terms_val and ("net 30" in terms_val.lower() or "net30" in terms_val.lower()):
                        reason = "Payment terms are Net 30 — compliant with policy."
                    elif terms_val and terms_val != "Unknown":
                        status = "FAIL"
                        reason = f"Payment term is '{terms_val}' — not Net 30 as required."
                    else:
                        reason = "Payment terms not specified; assuming compliant."

                elif code == "PAY-POL-04":
                    if "gst" in (contract_text + quote_text + email_text).lower():
                        reason = "GST details are referenced in the documents."
                    else:
                        status = "FAIL"
                        reason = "No GST details found in the submitted documents."

                elif code == "PAY-POL-05":
                    reason = "Finance verification is a process check — assumed compliant."

                # ── Procurement policies ─────────────────────────────────
                elif code == "PROC-POL-01":
                    if price_val and price_val > 1000000:
                        if not warranty_val or "3 year" not in warranty_val.lower():
                            status = "FAIL"
                            reason = f"Price ₹{price_val:,.0f} is above ₹10L threshold but 3-year warranty not confirmed."
                        else:
                            reason = "Price above ₹10L threshold and 3-year warranty confirmed."
                    else:
                        reason = "Procurement below ₹10L threshold; warranty check not required."

                elif code == "PROC-POL-02":
                    if "onsite" in (contract_text + quote_text + email_text).lower() or "on-site" in (contract_text + quote_text + email_text).lower():
                        reason = "Onsite support clause found in documents."
                    else:
                        status = "FAIL"
                        reason = "No onsite support commitment found in submitted documents."

                elif code == "PROC-POL-03":
                    quote_timeline = quote_data.delivery_timeline if quote_data else ""
                    email_days = quote_data.delivery_timeline if quote_data else ""
                    # Check for delivery day numbers
                    delivery_days = None
                    for doc in [contract_text, quote_text, email_text]:
                        import re
                        m = re.search(r'(\d+)\s*(?:working\s*)?days?', doc, re.IGNORECASE)
                        if m:
                            delivery_days = int(m.group(1))
                            break
                    if delivery_days is not None:
                        if delivery_days <= 21:
                            reason = f"Delivery committed at {delivery_days} working days — within 21-day policy limit."
                        else:
                            status = "FAIL"
                            reason = f"Delivery committed at {delivery_days} days — exceeds the 21-day policy limit."
                    else:
                        reason = "Delivery timeline not explicitly specified in documents."

                elif code == "PROC-POL-08":
                    if penalty_val and len(penalty_val.strip()) > 5:
                        reason = "Penalty clause present in contract."
                    else:
                        status = "FAIL"
                        reason = "No penalty clause found in contract — required by procurement policy."

                # ── SLA policies ─────────────────────────────────────────
                elif code == "SLA-POL-01":
                    if sla_val and ("99%" in sla_val or "99.9" in sla_val):
                        reason = "SLA uptime of 99%+ confirmed in contract."
                    elif sla_val and len(sla_val.strip()) > 5:
                        status = "FAIL"
                        reason = f"SLA terms found but 99% uptime not explicitly stated: '{sla_val[:80]}'"
                    else:
                        status = "FAIL"
                        reason = "No SLA uptime terms found in contract; 99% minimum required."

                elif code == "SLA-POL-02":
                    if sla_val and ("4 hour" in sla_val.lower() or "4-hour" in sla_val.lower()):
                        reason = "4-hour critical issue resolution confirmed in SLA."
                    elif sla_val:
                        reason = "SLA referenced but 4-hour critical resolution not explicitly confirmed."
                    else:
                        status = "FAIL"
                        reason = "No SLA terms for critical issue resolution found."

                # ── Vendor Selection policies ─────────────────────────────
                elif code == "VS-POL-02":
                    if "gst" in (contract_text + quote_text + email_text).lower() and ("gstin" in (contract_text + quote_text + email_text).lower() or "gst reg" in (contract_text + quote_text + email_text).lower()):
                        reason = "GSTIN registration details found in submitted documents."
                    else:
                        status = "FAIL"
                        reason = "No GST registration certificate (GSTIN) found in submitted documents."

                elif code == "VS-POL-03":
                    if "iso" in (contract_text + quote_text + email_text).lower():
                        reason = "ISO certification referenced in vendor documents."
                    else:
                        status = "FAIL"
                        reason = "No ISO certification mentioned in vendor documents."

                elif code == "VS-POL-04":
                    if "pan" in (contract_text + quote_text + email_text).lower():
                        reason = "PAN details referenced in vendor documents."
                    else:
                        status = "FAIL"
                        reason = "No PAN number found in vendor documents."

                else:
                    # For remaining policies: check if policy keyword appears in any document
                    keyword_hits = sum(1 for kw in text.lower().split() if len(kw) > 5 and kw in (contract_text + quote_text + email_text).lower())
                    if keyword_hits >= 2:
                        reason = "Policy requirements referenced in submitted documents."
                    else:
                        status = "FAIL"
                        reason = "Policy requirement not evidenced in submitted documents."

                policy_verdict.append(PolicyVerdictItem(
                    code=code,
                    category=category,
                    text=text[:120] + ("…" if len(text) > 120 else ""),
                    status=status,
                    reason=reason
                ))

        except Exception as db_err:
            print(f"[PolicyAgent] Policy verdict generation failed: {db_err}")
            policy_verdict = []

        # Build human-readable decision reason
        failed_policies = [p for p in policy_verdict if p.status == "FAIL"]
        passed_policies = [p for p in policy_verdict if p.status == "PASS"]
        
        if vendor_blacklisted:
            decision_reason = f"⛔ Vendor '{vendor_val}' is blacklisted and cannot be recommended."
        elif purchase_limit_exceeded and missing_docs:
            decision_reason = f"⚠️ Purchase amount (₹{price_val:,.0f}) exceeds policy limit AND required documents are missing ({', '.join(missing_docs)}). {len(failed_policies)} policy checks failed."
        elif purchase_limit_exceeded:
            decision_reason = f"⚠️ Purchase amount (₹{price_val:,.0f}) exceeds the ₹8.3L (≈$100k) policy limit — CFO approval required. {len(failed_policies)} policy checks failed."
        elif missing_docs:
            decision_reason = f"⚠️ Missing required documents: {', '.join(missing_docs)}. {len(failed_policies)} policy checks failed."
        elif failed_policies:
            top_fails = "; ".join([f"{p.code} ({p.reason})" for p in failed_policies[:3]])
            decision_reason = f"⚠️ {len(failed_policies)} policy checks failed: {top_fails}."
        else:
            decision_reason = f"✅ All {len(passed_policies)} checked policies passed. Vendor meets compliance requirements for approval."

        # Now run AI-enhanced analysis for compliance_status
        prompt = f"""
You are an expert enterprise Policy Compliance Agent.
Your task is to analyze matching policy records and matrix thresholds to determine if the deal is compliant, and identify required approvals.

Compliance Context:
- Seeded Guidelines: {matching_policies}
- Approval Matrix: {matrix}
- Vendor Blacklisted Status: {vendor_blacklisted}
- Purchase Limit Exceeded Status: {purchase_limit_exceeded}
- Missing Required Documents: {missing_docs}

Deal Parameters:
- Price: {price_val}
- Proposed Payment Terms: {terms_val}

Task:
Determine:
1. 'purchase_limit_exceeded': True if the deal exceeds buyer delegation limit ($100k).
2. 'approvals_required': Specific list of approvals required (e.g. Director, CFO signature needed).
3. 'vendor_blacklisted': Check if this vendor is marked as blacklisted.
4. 'missing_required_documents': The list of missing documents.
5. 'compliance_status': 'Compliant', 'Non-Compliant', or 'Conditional' compliance.
"""
        try:
            from app.core.llm import generate_structured_data
            # We need just the base fields from LLM, then merge in our verdict
            from app.schemas.agent_outputs import PolicyComplianceAgentOutput as PCAO
            import pydantic

            class _BaseOutput(pydantic.BaseModel):
                purchase_limit_exceeded: bool
                approvals_required: list
                vendor_blacklisted: bool
                missing_required_documents: list
                compliance_status: str

            base = await generate_structured_data(prompt, _BaseOutput)
            return PolicyComplianceAgentOutput(
                purchase_limit_exceeded=base.purchase_limit_exceeded,
                approvals_required=base.approvals_required,
                vendor_blacklisted=base.vendor_blacklisted,
                missing_required_documents=base.missing_required_documents,
                compliance_status=base.compliance_status,
                policy_verdict=policy_verdict,
                decision_reason=decision_reason
            )
        except Exception as e:
            # Fallback
            status = "Compliant"
            approvals = []
            if purchase_limit_exceeded or vendor_blacklisted or missing_docs or failed_policies:
                status = "Conditional"
                if purchase_limit_exceeded:
                    approvals.append("CFO approval required")
                if vendor_blacklisted:
                    approvals.append("VP of Procurement (Blacklist override)")
                if missing_docs:
                    approvals.append("Audit Compliance sign-off")
            
            return PolicyComplianceAgentOutput(
                purchase_limit_exceeded=purchase_limit_exceeded,
                approvals_required=approvals,
                vendor_blacklisted=vendor_blacklisted,
                missing_required_documents=missing_docs,
                compliance_status=status,
                policy_verdict=policy_verdict,
                decision_reason=decision_reason
            )
