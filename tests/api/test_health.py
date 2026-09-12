from fastapi.testclient import TestClient
from src.api.main import app

client = TestClient(app)

def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"

def test_list_companies_endpoint():
    response = client.get("/api/v1/companies")
    assert response.status_code == 200
    assert len(response.json()) >= 92

def test_company_profile_found():
    response = client.get("/api/v1/companies/COMP_01")
    assert response.status_code == 200

def test_sectors_endpoint():
    response = client.get("/api/v1/sectors")
    assert response.status_code == 200
