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
@patch("app.db.table")
async def test_create_promotion(mock_table, client):
    mock_table.put_item = MagicMock()
    
    now = datetime.utcnow()
    payload = {
        "name": "Summer Sale",
        "promo_type": "PERCENT",
        "value": 10,
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=30)).isoformat(),
        "usage_limit": 100,
        "min_cart_value": 50.0,
        "applicable_categories": ["electronics"],
    }
    
    response = await client.post("/promotions", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Summer Sale"
    assert data["promo_type"] == "PERCENT"
    assert data["value"] == 10


@pytest.mark.asyncio
@patch("app.db.get_promotion")
async def test_get_promotion(mock_get, client):
    mock_get.return_value = {
        "promo_id": "test-id",
        "name": "Test Promo",
        "promo_type": "FIXED",
        "value": 25.0,
        "start_date": "2024-01-01T00:00:00",
        "end_date": "2024-12-31T23:59:59",
        "usage_limit": 50,
        "usage_count": 10,
        "min_cart_value": 0,
        "applicable_categories": [],
    }
    
    response = await client.get("/promotions/test-id")
    assert response.status_code == 200
    data = response.json()
    assert data["promo_id"] == "test-id"
    assert data["name"] == "Test Promo"


@pytest.mark.asyncio
@patch("app.db.get_promotion")
async def test_get_promotion_not_found(mock_get, client):
    mock_get.return_value = None
    
    response = await client.get("/promotions/nonexistent")
    assert response.status_code == 404
    data = response.json()
    assert data["title"] == "Not Found"


@pytest.mark.asyncio
@patch("app.db.list_active_promotions")
async def test_list_promotions(mock_list, client):
    now = datetime.utcnow()
    mock_list.return_value = [
        {
            "promo_id": "id1",
            "name": "Promo 1",
            "promo_type": "PERCENT",
            "value": 15,
            "start_date": (now - timedelta(days=10)).isoformat(),
            "end_date": (now + timedelta(days=10)).isoformat(),
            "usage_limit": 100,
            "usage_count": 5,
            "min_cart_value": 0,
            "applicable_categories": [],
        }
    ]
    
    response = await client.get("/promotions")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["name"] == "Promo 1"


@pytest.mark.asyncio
@patch("app.db.get_promotion_by_code")
async def test_validate_promo_success(mock_get, client):
    now = datetime.utcnow()
    mock_get.return_value = {
        "promo_id": "id1",
        "promo_type": "PERCENT",
        "value": 10,
        "start_date": (now - timedelta(days=1)).isoformat(),
        "end_date": (now + timedelta(days=1)).isoformat(),
        "usage_limit": 100,
        "usage_count": 5,
        "min_cart_value": 50.0,
        "applicable_categories": [],
    }
    
    with patch("app.db.get_user_promo_usage") as mock_usage:
        mock_usage.return_value = []
        
        payload = {
            "promo_code": "SUMMER10",
            "cart_total": 100.0,
            "user_id": "user123",
        }
        
        response = await client.post("/promotions/validate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["discount_amount"] == 10.0


@pytest.mark.asyncio
@patch("app.db.get_promotion_by_code")
async def test_validate_promo_not_found(mock_get, client):
    mock_get.return_value = None
    
    payload = {
        "promo_code": "INVALID",
        "cart_total": 100.0,
        "user_id": "user123",
    }
    
    response = await client.post("/promotions/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "not found" in data["message"].lower()


@pytest.mark.asyncio
@patch("app.db.get_promotion_by_code")
async def test_apply_promo_success(mock_get, client):
    now = datetime.utcnow()
    mock_get.return_value = {
        "promo_id": "id1",
        "promo_type": "FIXED",
        "value": 25.0,
        "start_date": (now - timedelta(days=1)).isoformat(),
        "end_date": (now + timedelta(days=1)).isoformat(),
        "usage_limit": 100,
        "usage_count": 5,
        "min_cart_value": 0,
        "applicable_categories": [],
    }
    
    with patch("app.db.get_user_promo_usage") as mock_usage:
        with patch("app.db.record_promo_usage") as mock_record:
            with patch("app.db.increment_promotion_usage") as mock_increment:
                mock_usage.return_value = []
                
                payload = {
                    "promo_code": "FIXED25",
                    "order_id": "order123",
                    "user_id": "user123",
                }
                
                response = await client.post("/promotions/apply", json=payload)
                assert response.status_code == 200
                data = response.json()
                assert data["applied"] is True
                assert data["discount_amount"] == 25.0
                mock_record.assert_called_once()
                mock_increment.assert_called_once()


@pytest.mark.asyncio
@patch("app.db.get_promotion_by_code")
async def test_apply_promo_usage_limit_exceeded(mock_get, client):
    now = datetime.utcnow()
    mock_get.return_value = {
        "promo_id": "id1",
        "promo_type": "PERCENT",
        "value": 10,
        "start_date": (now - timedelta(days=1)).isoformat(),
        "end_date": (now + timedelta(days=1)).isoformat(),
        "usage_limit": 5,
        "usage_count": 5,
        "min_cart_value": 0,
        "applicable_categories": [],
    }
    
    payload = {
        "promo_code": "LIMITED",
        "order_id": "order123",
        "user_id": "user123",
    }
    
    response = await client.post("/promotions/apply", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["applied"] is False
    assert "limit" in data["message"].lower()


@pytest.mark.asyncio
@patch("app.db.get_promotion_by_code")
async def test_apply_promo_already_used(mock_get, client):
    now = datetime.utcnow()
    mock_get.return_value = {
        "promo_id": "id1",
        "promo_type": "PERCENT",
        "value": 10,
        "start_date": (now - timedelta(days=1)).isoformat(),
        "end_date": (now + timedelta(days=1)).isoformat(),
        "usage_limit": 100,
        "usage_count": 10,
        "min_cart_value": 0,
        "applicable_categories": [],
    }
    
    with patch("app.db.get_user_promo_usage") as mock_usage:
        mock_usage.return_value = [{"order_id": "old_order"}]
        
        payload = {
            "promo_code": "USED",
            "order_id": "order123",
            "user_id": "user123",
        }
        
        response = await client.post("/promotions/apply", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["applied"] is False
        assert "already used" in data["message"].lower()
