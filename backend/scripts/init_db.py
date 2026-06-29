import sys
import os
import google.generativeai as genai

# Adjust sys.path to run as a standalone script from the backend directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.core.database import get_db_conn, create_tables

if settings.GEMINI_API_KEY:
    genai.configure(api_key=settings.GEMINI_API_KEY)

def get_vector_embedding(text: str) -> list:
    """
    Calls Google Gemini Embeddings API to generate a semantic representation.
    """
    if not settings.GEMINI_API_KEY:
        print("GEMINI_API_KEY not configured. Seeding dummy vectors...")
        return [0.0] * 3072
    try:
        response = genai.embed_content(
            model="models/gemini-embedding-001",
            content=text,
            task_type="retrieval_document"
        )
        return response["embedding"]
    except Exception as e:
        print(f"Error calling Gemini Embeddings API: {e}. Seeding dummy vectors...")
        return [0.0] * 3072

def seed_database():
    print("Initializing PostgreSQL database with pgvector extensions...")
    with get_db_conn() as conn:
        cursor = conn.cursor()
        
        # Clear existing tables for a clean seed using CASCADE for Postgres
        cursor.execute("DROP TABLE IF EXISTS audit_trail CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS purchase_history CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS vendor_catalog CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS vendors CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS procurement_sessions CASCADE;")
        cursor.execute("DROP TABLE IF EXISTS policies CASCADE;")
        conn.commit()
        
        # Create tables
        create_tables(conn)
        
        # Seed Policies with Vector Embeddings
        policies = [
            ("PROC-POL-01", "limits", "Any software transaction exceeding $100,000 must include at least two competitive quotes."),
            ("PROC-POL-02", "limits", "Purchases under $10,000 can be processed via standard corporate credit card without formal purchase orders."),
            ("PROC-POL-12", "payment_terms", "Standard payment terms are Net 30. Deviations to Net 45 require CFO approval. Deviations exceeding Net 45 require Board level approval."),
            ("SOP-SFT-02", "security", "InfoSec review is mandatory for all third-party software integrations handling customer data."),
            ("SOP-SFT-03", "escrow", "Source code escrow protection must be negotiated for proprietary vendor APIs that represent high operational dependencies."),
            ("PROC-POL-07", "approval", "Procurement Approval Matrix: Tier 1 (Manager) <= $25k; Tier 2 (Director) <= $100k; Tier 3 (VP & CFO) > $100k.")
        ]
        
        print("Seeding policies & generating semantic vector embeddings...")
        for code, category, text in policies:
            print(f" -> Generating embedding for policy: {code}...")
            vector = get_vector_embedding(text)
            vector_str = f"[{','.join(map(str, vector))}]"
            cursor.execute("""
            INSERT INTO policies (code, category, text, embedding)
            VALUES (%s, %s, %s, %s);
            """, (code, category, text, vector_str))
            
        conn.commit()
        print("Database initialized and seeded successfully in PostgreSQL!")

if __name__ == "__main__":
    seed_database()
