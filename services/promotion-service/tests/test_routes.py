import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "promotion-service"

@pytest.mark.asyncio
@patch("app.db.create_promotion")
@patch("app.db.get_promotion_by_id")
async def test_create_promotion(mock_get, mock_create, client):
    mock_create.return_value = "promo-123"
    mock_get.return_value = {
        "promo_id": "promo-123",
        "name": "Summer Sale",
        "promo_code": "SUMMER20",
        "promotion_type": "PERCENT",
        "value": 20.0,
        "start_date": "2024-01-01T00:00:00",
        "end_date": "2024-12-31T23:59:59",
        "usage_limit": 1000,
        "usage_count": 0,
        "min_cart_value": 50.0,
        "applicable_categories": ["electronics"]
    }
    
    now = datetime.utcnow()
    future = now + timedelta(days=30)
    
    payload = {
        "name": "Summer Sale",
        "promo_code": "SUMMER20",
        "promotion_type": "PERCENT",
        "value": 20.0,
        "start_date": now.isoformat(),
        "end_date": future.isoformat(),
        "usage_limit": 1000,
        "min_cart_value": 50.0,
        "applicable_categories": ["electronics"]
    }
    
    response = await client.post("/promotions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["promo_id"] == "promo-123"
    assert data["name"] == "Summer Sale"
    assert data["promotion_type"] == "PERCENT"

@pytest.mark.asyncio
async def test_create_promotion_invalid_dates(client):
    now = datetime.utcnow()
    past = now - timedelta(days=1)
    
    payload = {
        "name": "Invalid Promo",
        "promo_code": "INVALID",
        "promotion_type": "PERCENT",
        "value": 10.0,
        "start_date": now.isoformat(),
        "end_date": past.isoformat(),
        "usage_limit": 100
    }
    
    response = await client.post("/promotions", json=payload)
    assert response.status_code == 400

@pytest.mark.asyncio
@patch("app.db.get_promotion_by_id")
async def test_get_promotion(mock_get, client):
    mock_get.return_value = {
        "promo_id": "promo-456",
        "name": "Winter Deal",
        "promo_code": "WINTER15",
        "promotion_type": "FIXED",
        "value": 15.0,
        "start_date": "2024-01-01T00:00:00",
        "end_date": "2024-12-31T23:59:59",
        "usage_limit": 500,
        "usage_count": 100,
        "min_cart_value": 30.0,
        "applicable_categories": None
    }
    
    response = await client.get("/promotions/promo-456")
    assert response.status_code == 200
    data = response.json()
    assert data["promo_id"] == "promo-456"
    assert data["name"] == "Winter Deal"

@pytest.mark.asyncio
@patch("app.db.get_promotion_by_id")
async def test_get_promotion_not_found(mock_get, client):
    mock_get.return_value = None
    
    response = await client.get("/promotions/nonexistent")
    assert response.status_code == 404

@pytest.mark.asyncio
@patch("app.db.list_active_promotions")
async def test_list_active_promotions(mock_list, client):
    mock_list.return_value = [
        {
            "promo_id": "promo-1",
            "name": "Active Promo 1",
            "promo_code": "ACTIVE1",
            "promotion_type": "PERCENT",
            "value": 10.0,
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-12-31T23:59:59",
            "usage_limit": 1000,
            "usage_count": 50,
            "min_cart_value": None,
            "applicable_categories": None
        }
    ]
    
    response = await client.get("/promotions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Active Promo 1"

@pytest.mark.asyncio
@patch("app.db.get_promotion_by_code")
async def test_validate_promotion_valid(mock_get, client):
    mock_get.return_value = {
        "promo_id": "promo-789",
        "name": "Valid Promo",
        "promo_code": "VALID10",
        "promotion_type": "PERCENT",
        "value": 10.0,
        "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "usage_limit": 1000,
        "usage_count": 50,
        "min_cart_value": 50.0,
        "applicable_categories": None
    }
    
    payload = {
        "promo_code": "VALID10",
        "cart_total": 100.0,
        "user_id": "user-123"
    }
    
    response = await client.post("/promotions/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["discount_amount"] == 10.0

@pytest.mark.asyncio
@patch("app.db.get_promotion_by_code")
async def test_validate_promotion_not_found(mock_get, client):
    mock_get.return_value = None
    
    payload = {
        "promo_code": "NOTFOUND",
        "cart_total": 100.0,
        "user_id": "user-123"
    }
    
    response = await client.post("/promotions/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert data["message"] == "Promotion code not found"

@pytest.mark.asyncio
@patch("app.db.get_promotion_by_code")
async def test_validate_promotion_inactive(mock_get, client):
    mock_get.return_value = {
        "promo_id": "promo-old",
        "name": "Old Promo",
        "promo_code": "OLD123",
        "promotion_type": "PERCENT",
        "value": 5.0,
        "start_date": (datetime.utcnow() - timedelta(days=100)).isoformat(),
        "end_date": (datetime.utcnow() - timedelta(days=30)).isoformat(),
        "usage_limit": 100,
        "usage_count": 100,
        "min_cart_value": None,
        "applicable_categories": None
    }
    
    payload = {
        "promo_code": "OLD123",
        "cart_total": 100.0,
        "user_id": "user-123"
    }
    
    response = await client.post("/promotions/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False

@pytest.mark.asyncio
@patch("app.db.get_promotion_by_code")
async def test_validate_promotion_min_cart_value(mock_get, client):
    mock_get.return_value = {
        "promo_id": "promo-min",
        "name": "Min Cart Promo",
        "promo_code": "MINVAL",
        "promotion_type": "FIXED",
        "value": 20.0,
        "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "usage_limit": 1000,
        "usage_count": 0,
        "min_cart_value": 100.0,
        "applicable_categories": None
    }
    
    payload = {
        "promo_code": "MINVAL",
        "cart_total": 50.0,
        "user_id": "user-123"
    }
    
    response = await client.post("/promotions/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "Cart total must be at least" in data["message"]

@pytest.mark.asyncio
@patch("app.db.record_promo_usage")
@patch("app.db.increment_promotion_usage_count")
@patch("app.db.get_promotion_by_code")
async def test_apply_promotion_success(mock_get, mock_increment, mock_record, client):
    mock_get.return_value = {
        "promo_id": "promo-apply",
        "name": "Apply Promo",
        "promo_code": "APPLY20",
        "promotion_type": "PERCENT",
        "value": 20.0,
        "start_date": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "usage_limit": 1000,
        "usage_count": 100,
        "min_cart_value": None,
        "applicable_categories": None
    }
    mock_record.return_value = True
    mock_increment.return_value = True
    
    payload = {
        "promo_code": "APPLY20",
        "order_id": "order-456",
        "user_id": "user-123"
    }
    
    response = await client.post("/promotions/apply", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["applied"] is True
    assert data["message"] == "Promotion applied successfully"

@pytest.mark.asyncio
@patch("app.db.get_promotion_by_code")
async def test_apply_promotion_not_found(mock_get, client):
    mock_get.return_value = None
    
    payload = {
        "promo_code": "NOTFOUND",
        "order_id": "order-456",
        "user_id": "user-123"
    }
    
    response = await client.post("/promotions/apply", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["applied"] is False
