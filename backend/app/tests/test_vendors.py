from fastapi.testclient import TestClient
import sys
import os

# Adjust sys.path to run as a standalone script from the backend directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app.main import app, get_current_user

# Mock authentication dependency
app.dependency_overrides[get_current_user] = lambda: {"id": 1, "username": "test_user", "full_name": "Test User"}

client = TestClient(app)

def test_vendors_endpoints():
    print("Testing GET /api/v1/vendors...")
    response = client.get("/api/v1/vendors")
    assert response.status_code == 200
    vendors = response.json()
    assert len(vendors) > 0
    print(f"Success! Found {len(vendors)} vendors in DB.")
    
    # Select first vendor (e.g. Ananya Mehta or Suresh)
    vendor_name = vendors[0]["name"]
    print(f"Testing GET /api/v1/vendors/{vendor_name}...")
    response = client.get(f"/api/v1/vendors/{vendor_name}")
    assert response.status_code == 200
    details = response.json()
    assert "profile" in details
    assert "catalog" in details
    assert "purchase_history" in details
    print("Success! Vendor profile, catalog, and purchase history details fetched.")
    
    print("\nAll vendor API endpoints are working successfully!")

if __name__ == "__main__":
    test_vendors_endpoints()
