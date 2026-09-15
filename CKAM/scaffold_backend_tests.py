import os

def write_file(path, content):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content.strip() + '\n')

test_ml_py = """
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/api/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to MandiWise API"}

def test_get_mandis():
    response = client.get("/api/mandis/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_predict_price():
    # Assuming crop_id=1, mandi_id=1 exists
    response = client.post("/api/predict/", json={
        "crop_id": 1,
        "mandi_id": 1,
        "days_ahead": 7
    })
    assert response.status_code == 200
    data = response.json()
    assert "predicted_price" in data
    assert "current_price" in data
    
def test_compare_mandis():
    response = client.post("/api/recommendations/compare", json={
        "crop_id": 1,
        "quantity": 50,
        "unit": "quintal",
        "lat": 20.0,
        "lng": 78.0,
        "transport_rate_per_km": 10.0
    })
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    if len(data) > 0:
        assert data[0]["recommendation"] == "BEST MANDI"
"""
write_file('backend/tests/test_api.py', test_ml_py)
