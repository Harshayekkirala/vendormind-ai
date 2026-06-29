import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db_conn
from app.core.config import settings
import google.generativeai as genai

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

def get_vector_embedding(text: str) -> list:
    if not settings.GEMINI_API_KEY:
        print("  [WARN] No GEMINI_API_KEY - using zero vector.")
        return [0.0] * 3072
    try:
        response = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return response["embedding"]
    except Exception as e:
        print(f"  [WARN] Embedding failed: {e}. Using zero vector.")
        return [0.0] * 3072

POLICIES = [
    # ─── Cyber Security ────────────────────────────────────────────────
    ("SEC-POL-01", "security",
     "Vendor must comply with ISO 27001 information security management standards. "
     "Non-compliance results in automatic disqualification during procurement evaluation."),

    ("SEC-POL-02", "security",
     "Vendor must encrypt all confidential procurement data in transit and at rest "
     "using AES-256 or equivalent encryption standards."),

    ("SEC-POL-03", "security",
     "Vendor must maintain detailed access logs for all systems handling procurement "
     "data. Logs must be retained for a minimum of 12 months."),

    ("SEC-POL-04", "security",
     "Confidential procurement files and documents must not be shared externally "
     "without written authorization from the procurement head."),

    ("SEC-POL-05", "security",
     "Multi-factor authentication (MFA) is mandatory for all vendor personnel "
     "accessing shared procurement portals or systems."),

    ("SEC-POL-06", "security",
     "Vendor must report any security incidents or data breaches related to "
     "procurement data within 24 hours of detection to the procurement team."),

    # ─── Payment ───────────────────────────────────────────────────────
    ("PAY-POL-01", "payment_terms",
     "Advance payment to any vendor must not exceed 20% of the total contract value. "
     "Payments beyond this threshold require CFO approval."),

    ("PAY-POL-02", "payment_terms",
     "Standard preferred payment term is Net 30 Days from invoice receipt. "
     "Deviations require Finance department approval."),

    ("PAY-POL-03", "payment_terms",
     "Milestone-based payment structures are strongly encouraged for contracts "
     "exceeding ₹5 Lakhs to reduce financial risk."),

    ("PAY-POL-04", "payment_terms",
     "All vendor invoices must contain valid GST details including GSTIN, "
     "HSN/SAC codes, and applicable tax breakdowns."),

    ("PAY-POL-05", "approval",
     "All vendor payment approvals require formal Finance department verification "
     "before disbursement regardless of contract size."),

    # ─── Procurement ───────────────────────────────────────────────────
    ("PROC-POL-01", "limits",
     "Every laptop or hardware procurement above ₹10 Lakhs must include a "
     "minimum warranty of 3 years as a mandatory contract term."),

    ("PROC-POL-02", "limits",
     "Vendors must provide onsite support during the contract period. "
     "Remote-only support is not acceptable for hardware procurement contracts."),

    ("PROC-POL-03", "limits",
     "Delivery timeline must not exceed 21 working days from purchase order issuance. "
     "Delays beyond this incur penalties as per the contract penalty clause."),

    ("PROC-POL-04", "limits",
     "The procurement team must compare at least two vendor quotations before "
     "finalising any purchase. Single-source procurement requires Director approval."),

    ("PROC-POL-05", "limits",
     "Lowest price must not be the sole selection criterion. Vendor evaluation must "
     "consider quality, delivery timeline, support capability, and compliance history."),

    ("PROC-POL-06", "limits",
     "Vendors must demonstrate previous successful delivery experience with at least "
     "one comparable project as part of the selection process."),

    ("PROC-POL-07", "limits",
     "Warranty extension options are preferred and should be negotiated as part of "
     "the procurement contract terms where applicable."),

    ("PROC-POL-08", "limits",
     "A penalty clause must be present in all procurement contracts specifying "
     "financial penalties for delivery delays, SLA breaches, or non-compliance."),

    # ─── SLA ───────────────────────────────────────────────────────────
    ("SLA-POL-01", "limits",
     "Minimum service level agreement (SLA) uptime guaranteed by the vendor "
     "must be 99% or above. Below this threshold triggers contract review."),

    ("SLA-POL-02", "limits",
     "Critical system issues must be acknowledged and resolved by the vendor "
     "within 4 hours of reporting. Breach of this SLA activates penalty clauses."),

    ("SLA-POL-03", "limits",
     "Minor issues and service requests must be resolved by the vendor within "
     "24 hours. Repeated breaches are grounds for contract termination."),

    ("SLA-POL-04", "limits",
     "Vendor must provide quarterly performance and service delivery reports "
     "to the procurement and operations team for review."),

    ("SLA-POL-05", "limits",
     "Vendor must assign a dedicated support engineer for the duration of the "
     "contract as a single point of contact for issue escalation."),

    # ─── Vendor Selection ──────────────────────────────────────────────
    ("VS-POL-01", "limits",
     "Preferred vendors must maintain a vendor performance rating of 4 out of 5 "
     "or above based on past procurement evaluations and delivery history."),

    ("VS-POL-02", "limits",
     "All vendors must provide valid GST registration certificate (GSTIN) as a "
     "mandatory document during vendor onboarding and procurement submission."),

    ("VS-POL-03", "security",
     "Vendors must hold a valid ISO certification (e.g., ISO 9001 or ISO 27001) "
     "to be eligible for contracts involving IT, software, or security services."),

    ("VS-POL-04", "limits",
     "Vendors must provide their valid PAN (Permanent Account Number) details "
     "as a mandatory compliance document for all procurement contracts."),

    ("VS-POL-05", "limits",
     "Vendor must guarantee service availability above 99% as part of the "
     "service agreement. Lower availability commitments will disqualify the vendor."),

    ("VS-POL-06", "limits",
     "Vendor must offer dedicated technical support as part of their service "
     "offering. Generic helpdesk-only support is not acceptable."),

    ("VS-POL-07", "limits",
     "Vendor must provide faulty unit replacement within 3 working days for "
     "hardware contracts. Delays beyond this trigger the penalty clause."),
]


def seed_policies():
    print(f"\nSeeding {len(POLICIES)} policies into PostgreSQL...\n")
    inserted = 0
    skipped = 0

    with get_db_conn() as conn:
        cursor = conn.cursor()

        for code, category, text in POLICIES:
            # Skip if code already exists
            cursor.execute("SELECT id FROM policies WHERE code = %s;", (code,))
            if cursor.fetchone():
                print(f"  [SKIP] {code} already exists.")
                skipped += 1
                continue

            print(f"  [EMBED] {code} ({category})...")
            embedding = get_vector_embedding(text)
            vector_str = f"[{','.join(map(str, embedding))}]"

            cursor.execute("""
                INSERT INTO policies (code, category, text, embedding)
                VALUES (%s, %s, %s, %s);
            """, (code, category, text, vector_str))
            inserted += 1
            print(f"  [OK]    {code} inserted.")

        conn.commit()

    print(f"\nDone! {inserted} policies inserted, {skipped} skipped (already existed).\n")


if __name__ == "__main__":
    seed_policies()
