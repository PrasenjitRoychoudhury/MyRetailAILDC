import pytest
from httpx import AsyncClient
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock
from app.main import app
from app.models import PromotionType

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "promotion-service"}

@pytest.mark.asyncio
async def test_create_promotion(client):
    with patch("app.db.create_promotion", new_callable=AsyncMock) as mock_create:
        mock_create.return_value = True
        
        start_date = datetime.utcnow()
        end_date = start_date + timedelta(days=30)
        
        payload = {
            "promoCode": "SAVE10",
            "name": "Save 10 Percent",
            "promoType": "PERCENT",
            "value": 10.0,
            "startDate": start_date.isoformat(),
            "endDate": end_date.isoformat(),
            "usageLimit": 100,
            "minCartValue": 25.0,
            "applicableCategories": ["electronics", "books"],
        }
        
        response = await client.post("/promotions", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["promoCode"] == "SAVE10"
        assert "promoId" in data

@pytest.mark.asyncio
async def test_create_promotion_invalid_dates(client):
    end_date = datetime.utcnow()
    start_date = end_date + timedelta(days=30)
    
    payload = {
        "promoCode": "INVALID",
        "name": "Invalid Promo",
        "promoType": "PERCENT",
        "value": 10.0,
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "usageLimit": 100,
        "minCartValue": 0.0,
        "applicableCategories": [],
    }
    
    response = await client.post("/promotions", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert data["title"] == "Invalid Promotion Dates"

@pytest.mark.asyncio
async def test_get_promotion(client):
    mock_promo = {
        "promoId": "PROMOTION#123",
        "promoCode": "SAVE10",
        "name": "Save 10 Percent",
        "promoType": "PERCENT",
        "value": 10.0,
        "startDate": datetime.utcnow().isoformat(),
        "endDate": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "usageLimit": 100,
        "usageCount": 5,
        "minCartValue": 25.0,
        "applicableCategories": ["electronics"],
        "createdAt": datetime.utcnow().isoformat(),
    }
    
    with patch("app.db.get_promotion_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_promo
        
        response = await client.get("/promotions/PROMOTION#123")
        assert response.status_code == 200
        data = response.json()
        assert data["promoCode"] == "SAVE10"

@pytest.mark.asyncio
async def test_get_promotion_not_found(client):
    with patch("app.db.get_promotion_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        response = await client.get("/promotions/PROMOTION#999")
        assert response.status_code == 404
        data = response.json()
        assert data["title"] == "Not Found"

@pytest.mark.asyncio
async def test_list_promotions(client):
    mock_promos = [
        {
            "promoId": "PROMOTION#1",
            "promoCode": "SAVE10",
            "name": "Save 10 Percent",
            "promoType": "PERCENT",
            "value": 10.0,
            "startDate": datetime.utcnow().isoformat(),
            "endDate": (datetime.utcnow() + timedelta(days=30)).isoformat(),
            "usageLimit": 100,
            "usageCount": 5,
            "minCartValue": 25.0,
            "applicableCategories": [],
            "createdAt": datetime.utcnow().isoformat(),
        },
    ]
    
    with patch("app.db.list_active_promotions", new_callable=AsyncMock) as mock_list:
        mock_list.return_value = mock_promos
        
        response = await client.get("/promotions")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert len(data["promotions"]) == 1

@pytest.mark.asyncio
async def test_validate_promo_valid(client):
    mock_promo = {
        "promoId": "PROMOTION#1",
        "promoCode": "SAVE10",
        "promoType": "PERCENT",
        "value": 10.0,
        "startDate": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "endDate": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "usageLimit": 100,
        "usageCount": 5,
        "minCartValue": 25.0,
    }
    
    with patch("app.db.get_promotion_by_code", new_callable=AsyncMock) as mock_get:
        with patch("app.db.get_user_promo_usage", new_callable=AsyncMock) as mock_usage:
            mock_get.return_value = mock_promo
            mock_usage.return_value = None
            
            payload = {
                "promoCode": "SAVE10",
                "cartTotal": 100.0,
                "userId": "user123",
            }
            
            response = await client.post("/promotions/validate", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is True
            assert data["discountAmount"] == 10.0

@pytest.mark.asyncio
async def test_validate_promo_invalid_code(client):
    with patch("app.db.get_promotion_by_code", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        payload = {
            "promoCode": "INVALID",
            "cartTotal": 100.0,
            "userId": "user123",
        }
        
        response = await client.post("/promotions/validate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert data["message"] == "Invalid promo code"

@pytest.mark.asyncio
async def test_validate_promo_below_min_cart(client):
    mock_promo = {
        "promoId": "PROMOTION#1",
        "promoCode": "SAVE10",
        "promoType": "PERCENT",
        "value": 10.0,
        "startDate": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "endDate": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "usageLimit": 100,
        "usageCount": 5,
        "minCartValue": 50.0,
    }
    
    with patch("app.db.get_promotion_by_code", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_promo
        
        payload = {
            "promoCode": "SAVE10",
            "cartTotal": 30.0,
            "userId": "user123",
        }
        
        response = await client.post("/promotions/validate", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False
        assert "Cart total must be at least" in data["message"]

@pytest.mark.asyncio
async def test_validate_promo_already_used(client):
    mock_promo = {
        "promoId": "PROMOTION#1",
        "promoCode": "SAVE10",
        "promoType": "PERCENT",
        "value": 10.0,
        "startDate": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "endDate": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "usageLimit": 100,
        "usageCount": 5,
        "minCartValue": 25.0,
    }
    
    mock_usage = {"userId": "user123", "promoId": "PROMOTION#1"}
    
    with patch("app.db.get_promotion_by_code", new_callable=AsyncMock) as mock_get:
        with patch("app.db.get_user_promo_usage", new_callable=AsyncMock) as mock_usage_get:
            mock_get.return_value = mock_promo
            mock_usage_get.return_value = mock_usage
            
            payload = {
                "promoCode": "SAVE10",
                "cartTotal": 100.0,
                "userId": "user123",
            }
            
            response = await client.post("/promotions/validate", json=payload)
            assert response.status_code == 200
            data = response.json()
            assert data["valid"] is False
            assert "already used" in data["message"]

@pytest.mark.asyncio
async def test_apply_promo_success(client):
    mock_promo = {
        "promoId": "PROMOTION#1",
        "promoCode": "SAVE10",
        "promoType": "FIXED",
        "value": 5.0,
        "startDate": (datetime.utcnow() - timedelta(days=1)).isoformat(),
        "endDate": (datetime.utcnow() + timedelta(days=30)).isoformat(),
        "usageLimit": 100,
        "usageCount": 5,
        "minCartValue": 0.0,
        "SK": "METADATA#SAVE10",
    }
    
    with patch("app.db.get_promotion_by_code", new_callable=AsyncMock) as mock_get:
        with patch("app.db.get_user_promo_usage", new_callable=AsyncMock) as mock_usage:
            with patch("app.db.record_promo_usage", new_callable=AsyncMock) as mock_record:
                with patch("app.db.increment_usage_count", new_callable=AsyncMock) as mock_inc:
                    mock_get.return_value = mock_promo
                    mock_usage.return_value = None
                    mock_record.return_value = True
                    mock_inc.return_value = True
                    
                    payload = {
                        "promoCode": "SAVE10",
                        "orderId": "order123",
                        "userId": "user123",
                    }
                    
                    response = await client.post("/promotions/apply", json=payload)
                    assert response.status_code == 200
                    data = response.json()
                    assert data["applied"] is True
                    assert data["discountAmount"] == 5.0

@pytest.mark.asyncio
async def test_apply_promo_invalid_code(client):
    with patch("app.db.get_promotion_by_code", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        payload = {
            "promoCode": "INVALID",
            "orderId": "order123",
            "userId": "user123",
        }
        
        response = await client.post("/promotions/apply", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["applied"] is False
        assert data["message"] == "Invalid promo code"
