import sys
import os

# Adjust sys.path to run as a standalone script from the backend directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import get_db_conn

def seed_vendor_details():
    print("Seeding vendor catalog and purchase history into PostgreSQL...")
    with get_db_conn() as conn:
        cursor = conn.cursor()
        
        # 1. Fetch existing vendors to map by name
        cursor.execute("SELECT id, name FROM vendors;")
        vendors = cursor.fetchall()
        vendor_map = {v["name"].lower(): v["id"] for v in vendors}
        
        if not vendor_map:
            print("No vendors found in the database. Please run analysis or ensure vendors exist first.")
            return

        # Clear existing catalog and purchase history to avoid duplicates
        cursor.execute("DELETE FROM purchase_history;")
        cursor.execute("DELETE FROM vendor_catalog;")
        conn.commit()

        # Mock catalog data
        catalogs = {
            "ananya mehta": [
                ("API Integration License", 12000.0, 5),
                ("Cloud Data Storage Core", 45000.0, 2)
            ],
            "rohit deshmukh": [
                ("Custom UI Design Consultancy (hourly)", 150.0, 7),
                ("Vite React Framework Setup", 5000.0, 3)
            ],
            "suresh": [
                ("Database Maintenance Service", 8000.0, 4),
                ("Migration Support Package", 15000.0, 10)
            ],
            "neha kapoor": [
                ("Premium QA Testing Suite", 25000.0, 14),
                ("Automated Regression Pack", 10000.0, 7)
            ],
            "amit verma": [
                ("Security Compliance Audit", 35000.0, 21),
                ("Penetration Testing Service", 18000.0, 10)
            ],
            "priya nair": [
                ("Technical Writing SLA", 5000.0, 3),
                ("API Documentation Pack", 7500.0, 7)
            ],
            "alpha": [
                ("Enterprise Support Contract", 50000.0, 1),
                ("Standard Software Subscription", 2500.0, 1)
            ],
            "beta": [
                ("Standard License Support SLA", 15000.0, 3),
                ("Advanced Operations Package", 30000.0, 5)
            ]
        }

        # Mock purchase history data
        purchase_histories = {
            "ananya mehta": [
                ("PO-2025-010", "2025-03-12", 12000.0, 1, 12000.0, "Completed", 4.8),
                ("PO-2025-081", "2025-08-01", 60000.0, 5, 12000.0, "Completed", 4.5)
            ],
            "rohit deshmukh": [
                ("PO-2025-021", "2025-04-18", 7500.0, 50, 150.0, "Completed", 4.9)
            ],
            "suresh": [
                ("PO-2025-034", "2025-05-22", 8000.0, 1, 8000.0, "Completed", 4.2),
                ("PO-2026-004", "2026-01-15", 15000.0, 1, 15000.0, "Completed", 4.7)
            ],
            "neha kapoor": [
                ("PO-2025-055", "2025-06-30", 25000.0, 1, 25000.0, "Completed", 4.6)
            ],
            "amit verma": [
                ("PO-2025-072", "2025-07-15", 35000.0, 1, 35000.0, "Completed", 4.8)
            ],
            "priya nair": [
                ("PO-2025-090", "2025-09-10", 5000.0, 1, 5000.0, "Completed", 4.9)
            ],
            "alpha": [
                ("PO-2025-104", "2025-11-05", 50000.0, 1, 50000.0, "Completed", 4.4)
            ],
            "beta": [
                ("PO-2025-119", "2025-12-02", 15000.0, 1, 15000.0, "Completed", 4.3)
            ]
        }

        # Seed Catalogs
        for v_name, items in catalogs.items():
            if v_name in vendor_map:
                v_id = vendor_map[v_name]
                for desc, price, lead in items:
                    cursor.execute("""
                        INSERT INTO vendor_catalog (vendor_id, item_description, standard_unit_price, typical_lead_time_days)
                        VALUES (%s, %s, %s, %s);
                    """, (v_id, desc, price, lead))
        
        # Seed Purchase History
        for v_name, purchases in purchase_histories.items():
            if v_name in vendor_map:
                v_id = vendor_map[v_name]
                for po_id, date, amount, qty, u_price, status, rating in purchases:
                    cursor.execute("""
                        INSERT INTO purchase_history (vendor_id, purchase_id, date, amount, qty, unit_price, status, rating)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s);
                    """, (v_id, po_id, date, amount, qty, u_price, status, rating))

        conn.commit()
        print("Vendor catalogs and purchase histories seeded successfully!")

if __name__ == "__main__":
    seed_vendor_details()
