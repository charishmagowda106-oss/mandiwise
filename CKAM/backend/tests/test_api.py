from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models.models import User
from uuid import uuid4

client = TestClient(app)

def test_read_root():
    response = client.get("/api/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to MandiWise API"}

def test_get_mandis():
    response = client.get("/api/mandis/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)

def test_get_crops():
    response = client.get("/api/crops/")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_auth_workflow():
    email = f"test-{uuid4().hex}@example.com"
    payload = {"name": "Test Farmer", "email": email, "password": "test-pass-123", "location_lat": 20.0, "location_lng": 78.0}
    try:
        register = client.post("/api/auth/register", json=payload)
        assert register.status_code == 200

        login = client.post("/api/auth/login", data={"username": email, "password": payload["password"]})
        assert login.status_code == 200
        token = login.json()["access_token"]

        me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert me.status_code == 200
        assert me.json()["email"] == email
    finally:
        db = SessionLocal()
        db.query(User).filter(User.email == email).delete()
        db.commit()
        db.close()

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
    assert data["current_price"] > 0
    
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
        for result in data:
            assert result["expected_revenue"] == round(result["current_price"] * 50, 2)
            assert result["estimated_profit"] == round(result["expected_revenue"] - result["transport_cost"], 2)

def test_price_history():
    response = client.get("/api/prices/history", params={"crop_id": 1, "mandi_id": 1})
    assert response.status_code == 200
    data = response.json()
    assert data["crop"] and data["mandi"]
    assert len(data["points"]) > 0
    point = data["points"][0]
    assert set(point.keys()) == {"date", "min_price", "max_price", "modal_price"}
    # Oldest -> newest so trend charts draw left to right
    dates = [item["date"] for item in data["points"]]
    assert dates == sorted(dates)
    # Unknown ids must fail with a clear message, not an empty chart
    missing = client.get("/api/prices/history", params={"crop_id": 999999, "mandi_id": 1})
    assert missing.status_code == 404
