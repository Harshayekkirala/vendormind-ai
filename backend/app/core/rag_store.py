from typing import List, Dict, Any
import google.generativeai as genai
from app.core.config import settings
from app.core.database import get_db_conn

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

class RAGStore:
    def __init__(self):
        # Blacklisted vendors registry
        self.blacklisted_vendors = ["blacklisted inc", "fraud corp", "unsafe vendors llc"]

        # Premium seeded corporate policies for procurement check
        self.policies = [
            {
                "code": "PROC-POL-01",
                "category": "limits",
                "text": "Any software transaction exceeding $100,000 must include at least two competitive quotes."
            },
            {
                "code": "PROC-POL-02",
                "category": "limits",
                "text": "Purchases under $10,000 can be processed via standard corporate credit card without formal purchase orders."
            },
            {
                "code": "PROC-POL-12",
                "category": "payment_terms",
                "text": "Standard payment terms are Net 30. Deviations to Net 45 require CFO approval. Deviations exceeding Net 45 require Board level approval."
            },
            {
                "code": "SOP-SFT-02",
                "category": "security",
                "text": "InfoSec review is mandatory for all third-party software integrations handling customer data."
            },
            {
                "code": "SOP-SFT-03",
                "category": "escrow",
                "text": "Source code escrow protection must be negotiated for proprietary vendor APIs that represent high operational dependencies."
            },
            {
                "code": "PROC-POL-07",
                "category": "approval",
                "text": "Procurement Approval Matrix: Tier 1 (Manager) <= $25k; Tier 2 (Director) <= $100k; Tier 3 (VP & CFO) > $100k."
            }
        ]

    def search_policies(self, query: str) -> List[str]:
        try:
            # 1. Compute embedding of the query using Gemini API
            if not settings.GEMINI_API_KEY:
                raise ValueError("GEMINI_API_KEY not configured")
                
            response = genai.embed_content(
                model="models/gemini-embedding-001",
                content=query,
                task_type="retrieval_query"
            )
            query_vector = response["embedding"]
            query_vector_str = f"[{','.join(map(str, query_vector))}]"
            
            # 2. Query PostgreSQL with pgvector cosine distance
            matched = []
            with get_db_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT code, text, (embedding <=> %s) AS distance
                    FROM policies
                    ORDER BY distance ASC
                    LIMIT 3;
                """, (query_vector_str,))
                
                rows = cursor.fetchall()
                for row in rows:
                    matched.append(f"{row['code']}: {row['text']}")
                    
            if matched:
                return matched
        except Exception as e:
            print(f"pgvector search failed, falling back to keyword search: {e}")
            
        # Fallback to local keyword search
        query_words = set(query.lower().split())
        matched = []
        for policy in self.policies:
            policy_words = policy["text"].lower()
            match_score = sum(1 for w in query_words if w in policy_words)
            if match_score > 0:
                matched.append(f"{policy['code']}: {policy['text']}")
        
        if not matched:
            return [
                f"{self.policies[0]['code']}: {self.policies[0]['text']}",
                f"{self.policies[2]['code']}: {self.policies[2]['text']}",
                f"{self.policies[5]['code']}: {self.policies[5]['text']}"
            ]
        return matched

    def get_approval_matrix(self) -> Dict[str, Any]:
        return {
            "tier_1_limit": 25000.0,
            "tier_2_limit": 100000.0,
            "tier_3_limit": 1000000.0,
            "standards": "Net 30 terms, competitive bidding required above $100,000"
        }

    def is_vendor_blacklisted(self, vendor_name: str) -> bool:
        if not vendor_name:
            return False
        return vendor_name.lower().strip() in self.blacklisted_vendors

    def check_purchase_limit_exceeded(self, amount: float) -> bool:
        # Standard default corporate threshold limit for standard buyers without CFO sign-off is $100k
        return amount > 100000.0

    def get_required_documents(self, amount: float) -> List[str]:
        reqs = ["quotation"]
        if amount > 10000.0:
            reqs.append("contract")
        if amount > 100000.0:
            # Need competitive bidding docs
            reqs.append("competitive_bid_1")
        return reqs

rag_store = RAGStore()
