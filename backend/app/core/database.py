import psycopg
from psycopg.rows import dict_row
from contextlib import contextmanager
from app.core.config import settings

@contextmanager
def get_db_conn():
    """
    Context manager to safely open and close a connection to the PostgreSQL database.
    Enables dictionary-like row factory for easy column name retrieval.
    """
    conn = psycopg.connect(settings.DATABASE_URL, row_factory=dict_row)
    try:
        yield conn
    finally:
        conn.close()

def create_tables(conn):
    """
    Creates tables if they do not exist in PostgreSQL:
    - vendors: profile & status
    - purchase_history: past transactions
    - vendor_catalog: offering registry
    - audit_trail: transaction review actions
    - procurement_sessions: active workflow session states
    - policies: semantic policy library with pgvector embeddings
    """
    cursor = conn.cursor()
    
    # 0. Enable pgvector extension
    cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
    
    # 1. Procurement sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS procurement_sessions (
        session_id VARCHAR(100) PRIMARY KEY,
        requirements TEXT,
        rejected_vendors TEXT,
        approved_vendor VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 2. Semantic policies table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS policies (
        id SERIAL PRIMARY KEY,
        code VARCHAR(50) UNIQUE NOT NULL,
        category VARCHAR(50) NOT NULL,
        text TEXT NOT NULL,
        embedding VECTOR(3072)
    );
    """)

    # 3. Users table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        username VARCHAR(100) UNIQUE NOT NULL,
        hashed_password VARCHAR(255) NOT NULL,
        salt VARCHAR(64) NOT NULL,
        full_name VARCHAR(100),
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 4. User sessions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS user_sessions (
        id SERIAL PRIMARY KEY,
        user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        token VARCHAR(64) UNIQUE NOT NULL,
        expires_at TIMESTAMP NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)

    # 5. Vendors table (references users(id))
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendors (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        category VARCHAR(100) NOT NULL,
        performance_score REAL NOT NULL DEFAULT 0.0,
        risk_level VARCHAR(20) NOT NULL DEFAULT 'Low',
        is_blacklisted INTEGER NOT NULL DEFAULT 0,
        status VARCHAR(20) NOT NULL DEFAULT 'Active',
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
        UNIQUE (name, user_id)
    );
    """)
    
    # 6. Purchase history table (references vendors(id))
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchase_history (
        id SERIAL PRIMARY KEY,
        vendor_id INTEGER NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
        purchase_id VARCHAR(50) UNIQUE NOT NULL,
        date VARCHAR(20) NOT NULL,
        amount REAL NOT NULL,
        qty INTEGER NOT NULL,
        unit_price REAL NOT NULL,
        status VARCHAR(100) NOT NULL,
        rating REAL NOT NULL
    );
    """)
    
    # 7. Vendor catalog table (references vendors(id))
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vendor_catalog (
        id SERIAL PRIMARY KEY,
        vendor_id INTEGER NOT NULL REFERENCES vendors(id) ON DELETE CASCADE,
        item_description TEXT NOT NULL,
        standard_unit_price REAL NOT NULL,
        typical_lead_time_days INTEGER NOT NULL
    );
    """)

    # 8. Audit trail table (references users(id))
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS audit_trail (
        id SERIAL PRIMARY KEY,
        session_id VARCHAR(100) NOT NULL,
        vendor_name VARCHAR(100) NOT NULL,
        action VARCHAR(50) NOT NULL,
        notes TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
    );
    """)
    
    # Run migrations dynamically for existing databases
    try:
        # Migrate vendors table
        cursor.execute("ALTER TABLE vendors ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;")
        cursor.execute("ALTER TABLE vendors DROP CONSTRAINT IF EXISTS vendors_name_key;")
        cursor.execute("ALTER TABLE vendors DROP CONSTRAINT IF EXISTS vendors_name_user_id_key;")
        cursor.execute("ALTER TABLE vendors ADD CONSTRAINT vendors_name_user_id_key UNIQUE (name, user_id);")
        
        # Migrate audit_trail table
        cursor.execute("ALTER TABLE audit_trail ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE;")
    except Exception as e:
        print(f"Migration: Error modifying database tables: {e}")
        
    conn.commit()


# Session Serialization Helpers
def save_session_state(session_id: str, requirements: dict, rejected_vendors: list, approved_vendor: str = None):
    import json
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO procurement_sessions (session_id, requirements, rejected_vendors, approved_vendor)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT(session_id) DO UPDATE SET
                requirements = EXCLUDED.requirements,
                rejected_vendors = EXCLUDED.rejected_vendors,
                approved_vendor = EXCLUDED.approved_vendor;
        """, (
            session_id,
            json.dumps(requirements),
            ",".join(rejected_vendors),
            approved_vendor
        ))
        conn.commit()

def load_session_state(session_id: str) -> dict:
    import json
    with get_db_conn() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM procurement_sessions WHERE session_id = %s", (session_id,))
        row = cursor.fetchone()
        if row:
            return {
                "session_id": row["session_id"],
                "requirements": json.loads(row["requirements"] or "{}"),
                "rejected_vendors": [v for v in (row["rejected_vendors"] or "").split(",") if v],
                "approved_vendor": row["approved_vendor"]
            }
        return None


