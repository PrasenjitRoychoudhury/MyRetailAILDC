import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from app.main import app
from unittest.mock import patch, AsyncMock


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "promotion-service"


@pytest.mark.asyncio
async def test_create_promotion_success(client):
    payload = {
        "name": "Summer Sale",
        "promo_code": "SUMMER2024",
        "promotion_type": "PERCENT",
        "value": 10,
        "start_date": (datetime.utcnow()).isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "usage_limit": 100,
        "min_cart_value": 50,
        "applicable_categories": ["electronics"]
    }
    
    with patch("app.db.table.put_item", new_callable=AsyncMock):
        response = await client.post("/promotions", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Summer Sale"
        assert data["promo_code"] == "SUMMER2024"
        assert data["promotion_type"] == "PERCENT"


@pytest.mark.asyncio
async def test_create_promotion_invalid_dates(client):
    payload = {
        "name": "Invalid Sale",
        "promo_code": "INVALID",
        "promotion_type": "FIXED",
        "value": 10,
        "start_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "end_date": (datetime.utcnow()).isoformat(),
        "usage_limit": 100
    }
    
    response = await client.post("/promotions", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "Invalid Date Range" in data["title"]


@pytest.mark.asyncio
async def test_get_promotion_success(client):
    mock_promo = {
        "pk": "PROMOTION#abc123",
        "sk": "METADATA",
        "name": "Test Promo",
        "promo_code": "TEST123",
        "promotion_type": "PERCENT",
        "value": 15,
        "start_date": (datetime.utcnow()).isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "usage_limit": 50,
        "usage_count": 5,
        "min_cart_value": 25,
        "applicable_categories": ["books"]
    }
    
    with patch("app.db.get_promotion_by_id", new_callable=AsyncMock, return_value=mock_promo):
        response = await client.get("/promotions/PROMOTION#abc123")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "Test Promo"
        assert data["promo_code"] == "TEST123"
        assert data["is_active"] == True


@pytest.mark.asyncio
async def test_get_promotion_not_found(client):
    with patch("app.db.get_promotion_by_id", new_callable=AsyncMock, return_value=None):
        response = await client.get("/promotions/PROMOTION#notfound")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()


@pytest.mark.asyncio
async def test_list_promotions(client):
    mock_promos = [
        {
            "pk": "PROMOTION#promo1",
            "sk": "METADATA",
            "name": "Promo 1",
            "promo_code": "CODE1",
            "promotion_type": "PERCENT",
            "value": 10,
            "start_date": (datetime.utcnow()).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "usage_count": 0,
            "min_cart_value": 0
        },
        {
            "pk": "PROMOTION#promo2",
            "sk": "METADATA",
            "name": "Promo 2",
            "promo_code": "CODE2",
            "promotion_type": "FIXED",
            "value": 20,
            "start_date": (datetime.utcnow()).isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=14)).isoformat(),
            "usage_count": 0,
            "min_cart_value": 0
        }
    ]
    
    with patch("app.db.list_active_promotions", new_callable=AsyncMock, return_value=mock_promos):
        response = await client.get("/promotions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["promo_code"] == "CODE1"
        assert data[1]["promo_code"] == "CODE2"


@pytest.mark.asyncio
async def test_validate_promo_success(client):
    mock_promo = {
        "pk": "PROMOTION#abc123",
        "promo_code": "VALID10",
        "promotion_type": "PERCENT",
        "value": 10,
        "start_date": (datetime.utcnow()).isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "usage_limit": 100,
        "usage_count": 5,
        "min_cart_value": 50
    }
    
    payload = {
        "promo_code": "VALID10",
        "cart_total": 100,
        "user_id": "user123"
    }
    
    with patch("app.db.get_promotion_by_code", new_callable=AsyncMock, return_value=mock_promo), \
         patch("app.db.get_user_promo_usage", new_callable=AsyncMock, return_value=None):
        response = await client.post("/promotions/validate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert data["discount_amount"] == 10.0


@pytest.mark.asyncio
async def test_validate_promo_not_found(client):
    payload = {
        "promo_code": "NOTFOUND",
        "cart_total": 100,
        "user_id": "user123"
    }
    
    with patch("app.db.get_promotion_by_code", new_callable=AsyncMock, return_value=None):
        response = await client.post("/promotions/validate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        assert "not found" in data["message"].lower()


@pytest.mark.asyncio
async def test_validate_promo_expired(client):
    mock_promo = {
        "pk": "PROMOTION#abc123",
        "promo_code": "EXPIRED",
        "promotion_type": "PERCENT",
        "value": 10,
        "start_date": (datetime.utcnow() - timedelta(days=14)).isoformat(),
        "end_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
        "usage_limit": 100,
        "usage_count": 50,
        "min_cart_value": 0
    }
    
    payload = {
        "promo_code": "EXPIRED",
        "cart_total": 100,
        "user_id": "user123"
    }
    
    with patch("app.db.get_promotion_by_code", new_callable=AsyncMock, return_value=mock_promo):
        response = await client.post("/promotions/validate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        assert "not active" in data["message"].lower()


@pytest.mark.asyncio
async def test_validate_promo_min_cart_value(client):
    mock_promo = {
        "pk": "PROMOTION#abc123",
        "promo_code": "MINVAL",
        "promotion_type": "FIXED",
        "value": 20,
        "start_date": (datetime.utcnow()).isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "usage_limit": 100,
        "usage_count": 0,
        "min_cart_value": 100
    }
    
    payload = {
        "promo_code": "MINVAL",
        "cart_total": 50,
        "user_id": "user123"
    }
    
    with patch("app.db.get_promotion_by_code", new_callable=AsyncMock, return_value=mock_promo):
        response = await client.post("/promotions/validate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        assert "minimum requirement" in data["message"].lower()


@pytest.mark.asyncio
async def test_validate_promo_limit_reached(client):
    mock_promo = {
        "pk": "PROMOTION#abc123",
        "promo_code": "LIMITED",
        "promotion_type": "PERCENT",
        "value": 10,
        "start_date": (datetime.utcnow()).isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "usage_limit": 10,
        "usage_count": 10,
        "min_cart_value": 0
    }
    
    payload = {
        "promo_code": "LIMITED",
        "cart_total": 100,
        "user_id": "user123"
    }
    
    with patch("app.db.get_promotion_by_code", new_callable=AsyncMock, return_value=mock_promo):
        response = await client.post("/promotions/validate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        assert "usage limit" in data["message"].lower()


@pytest.mark.asyncio
async def test_validate_promo_already_used(client):
    mock_promo = {
        "pk": "PROMOTION#abc123",
        "promo_code": "ONCE",
        "promotion_type": "PERCENT",
        "value": 10,
        "start_date": (datetime.utcnow()).isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "usage_limit": 100,
        "usage_count": 50,
        "min_cart_value": 0
    }
    
    mock_usage = {
        "pk": "PROMO_USAGE#user123#PROMOTION#abc123",
        "user_id": "user123",
        "promo_id": "PROMOTION#abc123",
        "used_at": datetime.utcnow().isoformat()
    }
    
    payload = {
        "promo_code": "ONCE",
        "cart_total": 100,
        "user_id": "user123"
    }
    
    with patch("app.db.get_promotion_by_code", new_callable=AsyncMock, return_value=mock_promo), \
         patch("app.db.get_user_promo_usage", new_callable=AsyncMock, return_value=mock_usage):
        response = await client.post("/promotions/validate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == False
        assert "already used" in data["message"].lower()


@pytest.mark.asyncio
async def test_apply_promo_success(client):
    mock_promo = {
        "pk": "PROMOTION#abc123",
        "promo_code": "APPLY10",
        "promotion_type": "PERCENT",
        "value": 10,
        "start_date": (datetime.utcnow()).isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "usage_limit": 100,
        "usage_count": 5,
        "min_cart_value": 0
    }
    
    payload = {
        "promo_code": "APPLY10",
        "order_id": "order123",
        "user_id": "user123"
    }
    
    with patch("app.db.get_promotion_by_code", new_callable=AsyncMock, return_value=mock_promo), \
         patch("app.db.get_user_promo_usage", new_callable=AsyncMock, return_value=None), \
         patch("app.db.record_promo_usage", new_callable=AsyncMock), \
         patch("app.db.increment_usage_count", new_callable=AsyncMock):
        response = await client.post("/promotions/apply", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["applied"] == True
        assert data["discount_amount"] == 10.0


@pytest.mark.asyncio
async def test_apply_promo_not_found(client):
    payload = {
        "promo_code": "NOTEXIST",
        "order_id": "order123",
        "user_id": "user123"
    }
    
    with patch("app.db.get_promotion_by_code", new_callable=AsyncMock, return_value=None):
        response = await client.post("/promotions/apply", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["applied"] == False
        assert "not found" in data["message"].lower()


@pytest.mark.asyncio
async def test_apply_promo_expired(client):
    mock_promo = {
        "pk": "PROMOTION#abc123",
        "promo_code": "EXPIREDAPP",
        "promotion_type": "FIXED",
        "value": 20,
        "start_date": (datetime.utcnow() - timedelta(days=14)).isoformat(),
        "end_date": (datetime.utcnow() - timedelta(days=7)).isoformat(),
        "usage_limit": 100,
        "usage_count": 10,
        "min_cart_value": 0
    }
    
    payload = {
        "promo_code": "EXPIREDAPP",
        "order_id": "order123",
        "user_id": "user123"
    }
    
    with patch("app.db.get_promotion_by_code", new_callable=AsyncMock, return_value=mock_promo):
        response = await client.post("/promotions/apply", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["applied"] == False
        assert "not active" in data["message"].lower()


@pytest.mark.asyncio
async def test_apply_promo_already_used(client):
    mock_promo = {
        "pk": "PROMOTION#abc123",
        "promo_code": "ONCEONLY",
        "promotion_type": "PERCENT",
        "value": 15,
        "start_date": (datetime.utcnow()).isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "usage_limit": 100,
        "usage_count": 30,
        "min_cart_value": 0
    }
    
    mock_usage = {
        "pk": "PROMO_USAGE#user123#PROMOTION#abc123",
        "user_id": "user123",
        "promo_id": "PROMOTION#abc123",
        "used_at": datetime.utcnow().isoformat()
    }
    
    payload = {
        "promo_code": "ONCEONLY",
        "order_id": "order123",
        "user_id": "user123"
    }
    
    with patch("app.db.get_promotion_by_code", new_callable=AsyncMock, return_value=mock_promo), \
         patch("app.db.get_user_promo_usage", new_callable=AsyncMock, return_value=mock_usage):
        response = await client.post("/promotions/apply", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["applied"] == False
        assert "already used" in data["message"].lower()
