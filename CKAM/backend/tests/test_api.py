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


def _login(email, password):
    r = client.post("/api/auth/login", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_my_crops_workflow():
    """Create -> list (enriched) -> update -> delete a watched crop."""
    from datetime import date, timedelta
    from app.models.models import UserCrop

    email = f"mycrops-{uuid4().hex}@example.com"
    payload = {"name": "Ledger Farmer", "email": email, "password": "test-pass-123",
               "phone": make_phone(), "location_lat": 12.97, "location_lng": 77.59}
    assert client.post("/api/auth/register", json=payload).status_code == 200
    headers = _login(email, payload["password"])
    try:
        crop_id = client.get("/api/crops/").json()[0]["id"]
        harvest = date.today() + timedelta(days=20)
        created = client.post("/api/my-crops", headers=headers, json={
            "crop_id": crop_id, "quantity": 15,
            "sown_date": str(date.today() - timedelta(days=60)),
            "expected_harvest_date": str(harvest),
            "cost_seed": 2000, "cost_fertilizer": 4000, "cost_labor": 3000,
        })
        assert created.status_code == 201, created.text
        row = created.json()
        assert row["quantity"] == 15
        assert row["days_to_harvest"] == 20
        assert row["status"] == "growing"
        assert row["total_cost"] == 9000
        assert row["best"] is not None and row["best"]["mandi_name"]

        listed = client.get("/api/my-crops", headers=headers).json()
        assert len(listed) == 1 and listed[0]["id"] == row["id"]

        patched = client.patch(f"/api/my-crops/{row['id']}", headers=headers,
                               json={"quantity": 25, "expected_harvest_date": str(date.today() + timedelta(days=5))})
        assert patched.status_code == 200
        assert patched.json()["quantity"] == 25
        assert patched.json()["status"] == "soon"

        assert client.delete(f"/api/my-crops/{row['id']}", headers=headers).status_code == 204
        assert client.get("/api/my-crops", headers=headers).json() == []
    finally:
        db = SessionLocal()
        uid = db.query(User).filter(User.email == email).first()
        if uid:
            db.query(UserCrop).filter(UserCrop.user_id == uid.id).delete()
            db.query(User).filter(User.email == email).delete()
        db.commit(); db.close()


def test_my_crop_harvest_notification_fires_once():
    """A crop due within the harvest window notifies exactly once."""
    from datetime import date, timedelta
    from app.models.models import UserCrop, User as UserModel
    from app.services.alert_checker import evaluate_harvest_windows

    email = f"harvest-{uuid4().hex}@example.com"
    payload = {"name": "Harvest Farmer", "email": email, "password": "test-pass-123",
               "phone": make_phone(), "location_lat": 12.97, "location_lng": 77.59}
    assert client.post("/api/auth/register", json=payload).status_code == 200
    headers = _login(email, payload["password"])
    try:
        crop_id = client.get("/api/crops/").json()[0]["id"]
        created = client.post("/api/my-crops", headers=headers, json={
            "crop_id": crop_id, "quantity": 10,
            "expected_harvest_date": str(date.today() + timedelta(days=3)),
        })
        assert created.status_code == 201

        db = SessionLocal()
        try:
            assert evaluate_harvest_windows(db) >= 1   # window open -> notifies
            uc = db.query(UserCrop).join(UserModel, UserModel.id == UserCrop.user_id).filter(UserModel.email == email).first()
            assert uc.harvest_notified_at is not None
            assert evaluate_harvest_windows(db) == 0   # already notified -> silent
            notes = db.query(Notification).join(UserModel, UserModel.id == Notification.user_id).filter(UserModel.email == email).all()
            assert any(n.kind == "harvest_window" for n in notes)
        finally:
            db.close()
    finally:
        db = SessionLocal()
        u = db.query(User).filter(User.email == email).first()
        if u:
            db.query(Notification).filter(Notification.user_id == u.id).delete()
            db.query(UserCrop).filter(UserCrop.user_id == u.id).delete()
            db.query(User).filter(User.email == email).delete()
        db.commit(); db.close()


def test_my_crops_rejects_unknown_crop():
    email = f"mycrops-bad-{uuid4().hex}@example.com"
    payload = {"name": "Bad Crop", "email": email, "password": "test-pass-123", "phone": make_phone()}
    assert client.post("/api/auth/register", json=payload).status_code == 200
    headers = _login(email, payload["password"])
    try:
        response = client.post("/api/my-crops", headers=headers, json={"crop_id": 999999, "quantity": 5})
        assert response.status_code == 404
    finally:
        db = SessionLocal()
        u = db.query(User).filter(User.email == email).first()
        if u:
            db.query(User).filter(User.email == email).delete()
        db.commit(); db.close()
