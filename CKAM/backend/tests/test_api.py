from fastapi.testclient import TestClient
from app.main import app
from app.database.session import SessionLocal
from app.models.models import User, OtpCode, PriceAlert, Notification, Mandi
from uuid import uuid4
import secrets


def make_phone(prefix: str = "9") -> str:
    """A valid, effectively unique 10-digit Indian mobile number."""
    return prefix + f"{secrets.randbelow(10**9):09d}"

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
    payload = {"name": "Test Farmer", "email": email, "password": "test-pass-123",
               "phone": make_phone(), "location_lat": 20.0, "location_lng": 78.0}
    try:
        register = client.post("/api/auth/register", json=payload)
        assert register.status_code == 200
        assert register.json()["phone"].startswith("+91")

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

def test_register_rejects_bad_phone():
    payload = {"name": "Bad Phone", "email": f"test-{uuid4().hex}@example.com",
               "password": "test-pass-123", "phone": "12345"}
    response = client.post("/api/auth/register", json=payload)
    assert response.status_code == 422

def test_otp_login_workflow():
    """request-otp -> verify-otp -> authenticated, with no SMS/SMTP configured
    (dev mode exposes the code in the request-otp response)."""
    from app.services import notify
    email = f"otp-{uuid4().hex}@example.com"
    phone = make_phone()
    payload = {"name": "OTP Farmer", "email": email, "password": "test-pass-123", "phone": phone}
    try:
        assert client.post("/api/auth/register", json=payload).status_code == 200

        sent = client.post("/api/auth/request-otp", json={"phone": phone})
        assert sent.status_code == 200
        body = sent.json()
        assert body["masked_phone"].startswith("+91")
        if not notify.can_deliver():
            code = body["dev_code"]
            wrong = client.post("/api/auth/verify-otp", json={"phone": phone, "code": "000000" if code != "000000" else "111111"})
            assert wrong.status_code == 400  # wrong code rejected with a clear message
            ok = client.post("/api/auth/verify-otp", json={"phone": phone, "code": code})
            assert ok.status_code == 200
            token = ok.json()["access_token"]
            me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
            assert me.status_code == 200
            assert me.json()["email"] == email

        # Unlinked number must be refused up-front.
        unknown = client.post("/api/auth/request-otp", json={"phone": make_phone()})
        assert unknown.status_code == 404
    finally:
        db = SessionLocal()
        db.query(OtpCode).filter(OtpCode.destination == f"+91{phone}").delete()
        db.query(User).filter(User.email == email).delete()
        db.commit()
        db.close()

def test_alert_and_notifications():
    email = f"alert-{uuid4().hex}@example.com"
    phone = make_phone()
    payload = {"name": "Alert Farmer", "email": email, "password": "test-pass-123", "phone": phone}
    created_user = client.post("/api/auth/register", json=payload)
    assert created_user.status_code == 200
    login = client.post("/api/auth/login", data={"username": email, "password": payload["password"]})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    try:
        # Create without any location -> clear 400 (not a crash)
        no_loc = client.post("/api/alerts", json={"crop_id": 1, "quantity": 10}, headers=headers)
        assert no_loc.status_code == 400

        alert = client.post("/api/alerts", json={
            "crop_id": 1, "quantity": 10, "unit": "quintal",
            "lat": 12.97, "lng": 77.59, "transport_rate_per_km": 10,
            "min_profit": 1,
        }, headers=headers)
        assert alert.status_code == 201
        alert_id = alert.json()["id"]

        listed = client.get("/api/alerts", headers=headers)
        assert listed.status_code == 200 and len(listed.json()) == 1

        # Immediate check: threshold ₹1 is trivially met -> first run notifies.
        check = client.post(f"/api/alerts/{alert_id}/check", headers=headers)
        assert check.status_code == 200
        assert check.json()["notified"] is True
        assert check.json()["last_best_profit"] is not None

        notes = client.get("/api/notifications", headers=headers)
        assert notes.status_code == 200
        assert notes.json()["unread"] >= 1
        first_id = notes.json()["items"][0]["id"]

        assert client.post(f"/api/notifications/{first_id}/read", headers=headers).status_code == 200
        assert client.get("/api/notifications", headers=headers).json()["unread"] == 0

        # Another immediate check right away: same situation + cooldown -> no spam.
        again = client.post(f"/api/alerts/{alert_id}/check", headers=headers)
        assert again.json()["notified"] is False

        assert client.delete(f"/api/alerts/{alert_id}", headers=headers).status_code == 204
        assert client.get("/api/alerts", headers=headers).json() == []
    finally:
        db = SessionLocal()
        db.query(Notification).filter(Notification.user_id == created_user.json()["id"]).delete()
        db.query(PriceAlert).filter(PriceAlert.user_id == created_user.json()["id"]).delete()
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


def test_location_search_local_town(monkeypatch):
    """Local town list answers without any network call."""
    from app.api.endpoints import locations
    monkeypatch.setattr(locations, "_fetch_osm", lambda q, limit: [])
    locations._cache.clear()
    response = client.get("/api/locations/search", params={"q": "mysuru", "limit": 1})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == "mysuru"
    assert len(body["results"]) == 1
    place = body["results"][0]
    assert place["source"] in ("town", "mandi")  # mandis rank above towns on ties
    assert "mysuru" in (place["name"] + place["display"]).lower()
    assert isinstance(place["lat"], float) and isinstance(place["lng"], float)


def test_location_search_finds_mandi_from_db(monkeypatch):
    """A seeded mandi is found by name prefix."""
    from app.api.endpoints import locations
    monkeypatch.setattr(locations, "_fetch_osm", lambda q, limit: [])
    locations._cache.clear()
    db = SessionLocal()
    try:
        mandi = db.query(Mandi).first()
    finally:
        db.close()
    prefix = mandi.name[:4]
    response = client.get("/api/locations/search", params={"q": prefix, "limit": 15})
    assert response.status_code == 200
    sources = {item["source"] for item in response.json()["results"]}
    assert "mandi" in sources


def test_location_search_merges_osm_results(monkeypatch):
    """Unknown places fall through to the (mocked) OpenStreetMap results."""
    from app.api.endpoints import locations
    from app.api.endpoints.locations import PlaceResult
    fake = [PlaceResult(name="Samplepur", display="Samplepur, Karnataka, India",
                        lat=14.5, lng=76.0, source="osm")]
    monkeypatch.setattr(locations, "_fetch_osm", lambda q, limit: fake)
    locations._cache.clear()
    response = client.get("/api/locations/search", params={"q": "zzzz-unknown"})
    assert response.status_code == 200
    results = response.json()["results"]
    assert any(item["source"] == "osm" and item["name"] == "Samplepur" for item in results)


def test_location_search_rejects_too_short():
    response = client.get("/api/locations/search", params={"q": "a"})
    assert response.status_code == 422
