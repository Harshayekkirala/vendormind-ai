from typing import List, Dict, Any
from app.core.database import get_db_conn

class DBMemory:
    def __init__(self):
        # Static defaults for historical contextual outputs
        self.static_recommendations = [
            "PO-2025-081: Recommended asking for a volume discount because purchase quantity exceeded 50 units."
        ]
        self.static_feedback = [
            "PO-2025-081: Manager commented: 'volume discount recommendation was approved, saved $2,000 on final invoice.'"
        ]

    def get_vendor_history(self, vendor_name: str) -> List[Dict[str, Any]]:
        """
        Queries the local SQLite database for historical purchase records for a given vendor.
        Falls back to 'Generic Vendor' history if no records are found.
        """
        # Strip generic suffixes and lower-case to search
        cleaned_name = vendor_name.lower().replace("corp", "").replace("inc", "").replace("llc", "").strip()
        name_search = f"%{cleaned_name}%"
        
        try:
            with get_db_conn() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT ph.purchase_id, v.name as vendor_name, ph.date, ph.amount, ph.qty, ph.unit_price, ph.status, ph.rating
                    FROM purchase_history ph
                    JOIN vendors v ON ph.vendor_id = v.id
                    WHERE LOWER(v.name) LIKE %s;
                """, (name_search,))
                
                rows = cursor.fetchall()
                if rows:
                    return [dict(row) for row in rows]
                
                # Fallback to generic vendor if no matching vendor history is found
                cursor.execute("""
                    SELECT ph.purchase_id, v.name as vendor_name, ph.date, ph.amount, ph.qty, ph.unit_price, ph.status, ph.rating
                    FROM purchase_history ph
                    JOIN vendors v ON ph.vendor_id = v.id
                    WHERE LOWER(v.name) LIKE '%generic%';
                """)
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
        except Exception as e:
            print(f"Error querying vendor history from DB: {e}")
            return []

    def get_past_recommendations(self) -> List[str]:
        return self.static_recommendations

    def get_manager_feedback(self) -> List[str]:
        return self.static_feedback

db_memory = DBMemory()
