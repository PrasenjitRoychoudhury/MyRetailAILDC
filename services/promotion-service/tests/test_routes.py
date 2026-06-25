import pytest
from httpx import AsyncClient
from app.main import app
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, patch

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
async def test_create_promotion_success(client):
    tomorrow = datetime.utcnow() + timedelta(days=1)
    next_week = datetime.utcnow() + timedelta(days=7)
    
    payload = {
        "name": "Summer Sale",
        "type": "PERCENT",
        "value": 10.0,
        "start_date": datetime.utcnow().isoformat(),
        "end_date": next_week.isoformat(),
        "usage_limit": 100,
        "min_cart_value": 50.0,
        "applicable_categories": ["electronics", "clothing"]
    }
    
    with patch('app.routes.create_promotion', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = True
        response = await client.post(
            "/promotions",
            json=payload,
            headers={"x-admin-token": "valid_token"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Summer Sale"
        assert data["type"] == "PERCENT"
        assert data["value"] == 10.0

@pytest.mark.asyncio
async def test_create_promotion_missing_admin_token(client):
    payload = {
        "name": "Summer Sale",
        "type": "PERCENT",
        "value": 10.0,
        "start_date": datetime.utcnow().isoformat(),
        "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
        "usage_limit": 100
    }
    
    response = await client.post("/promotions", json=payload)
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_get_promotion_success(client):
    with patch('app.routes.get_promotion', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = {
            "promo_id": "test-promo-1",
            "name": "Test Promo",
            "type": "FIXED",
            "value": 25.0,
            "start_date": datetime.utcnow().isoformat(),
            "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
            "usage_limit": 50,
            "usage_count": 5,
            "min_cart_value": 100.0,
            "applicable_categories": ["all"],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }
        response = await client.get("/promotions/test-promo-1")
        assert response.status_code == 200
        data = response.json()
        assert data["promo_id"] == "test-promo-1"
        assert data["type"] == "FIXED"

@pytest.mark.asyncio
async def test_get_promotion_not_found(client):
    with patch('app.routes.get_promotion', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        response = await client.get("/promotions/nonexistent")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_promotion_success(client):
    with patch('app.routes.get_promotion', new_callable=AsyncMock) as mock_get:
        with patch('app.routes.update_promotion', new_callable=AsyncMock) as mock_update:
            mock_get.return_value = {
                "promo_id": "test-promo-1",
                "name": "Updated Promo",
                "type": "PERCENT",
                "value": 15.0,
                "start_date": datetime.utcnow().isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=10)).isoformat(),
                "usage_limit": 75,
                "usage_count": 5,
                "min_cart_value": 50.0,
                "applicable_categories": [],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
            mock_update.return_value = True
            
            response = await client.patch(
                "/promotions/test-promo-1",
                json={"name": "Updated Promo", "value": 15.0},
                headers={"x-admin-token": "valid_token"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["updated"] is True

@pytest.mark.asyncio
async def test_update_promotion_missing_admin_token(client):
    response = await client.patch(
        "/promotions/test-promo-1",
        json={"name": "Updated Promo"}
    )
    assert response.status_code == 403

@pytest.mark.asyncio
async def test_delete_promotion_success(client):
    with patch('app.routes.get_promotion', new_callable=AsyncMock) as mock_get:
        with patch('app.routes.delete_promotion', new_callable=AsyncMock) as mock_delete:
            mock_get.return_value = {"promo_id": "test-promo-1"}
            mock_delete.return_value = True
            
            response = await client.delete(
                "/promotions/test-promo-1",
                headers={"x-admin-token": "valid_token"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["deleted"] is True
            assert data["promo_id"] == "test-promo-1"

@pytest.mark.asyncio
async def test_delete_promotion_not_found(client):
    with patch('app.routes.get_promotion', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        response = await client.delete(
            "/promotions/nonexistent",
            headers={"x-admin-token": "valid_token"}
        )
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_validate_promo_valid(client):
    with patch('app.routes.validate_promo_code', new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = {
            "valid": True,
            "discount_amount": 15.0,
            "message": "Promotion is valid"
        }
        response = await client.post(
            "/promotions/validate",
            json={
                "promo_code": "SUMMER10",
                "cart_total": 150.0,
                "user_id": "user123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is True
        assert data["discount_amount"] == 15.0

@pytest.mark.asyncio
async def test_validate_promo_invalid(client):
    with patch('app.routes.validate_promo_code', new_callable=AsyncMock) as mock_validate:
        mock_validate.return_value = {
            "valid": False,
            "discount_amount": 0,
            "message": "Promotion code not found"
        }
        response = await client.post(
            "/promotions/validate",
            json={
                "promo_code": "INVALID",
                "cart_total": 100.0,
                "user_id": "user123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] is False

@pytest.mark.asyncio
async def test_apply_promo_success(client):
    with patch('app.routes.apply_promo_code', new_callable=AsyncMock) as mock_apply:
        mock_apply.return_value = {
            "applied": True,
            "discount_amount": 25.0,
            "message": "Promotion applied successfully"
        }
        response = await client.post(
            "/promotions/apply",
            json={
                "promo_code": "SUMMER10",
                "order_id": "order123",
                "user_id": "user123"
            }
        )
        assert response.status_code == 200
        data = response.json()
        assert data["applied"] is True
        assert data["discount_amount"] == 25.0

@pytest.mark.asyncio
async def test_apply_promo_failed(client):
    with patch('app.routes.apply_promo_code', new_callable=AsyncMock) as mock_apply:
        mock_apply.return_value = {
            "applied": False,
            "discount_amount": 0,
            "message": "Usage limit exceeded"
        }
        response = await client.post(
            "/promotions/apply",
            json={
                "promo_code": "EXPIRED",
                "order_id": "order123",
                "user_id": "user123"
            }
        )
        assert response.status_code == 400

@pytest.mark.asyncio
async def test_list_active_promotions(client):
    with patch('app.routes.list_active_promotions', new_callable=AsyncMock) as mock_list:
        mock_list.return_value = [
            {
                "promo_id": "promo1",
                "name": "Promo 1",
                "type": "PERCENT",
                "value": 10.0,
                "start_date": datetime.utcnow().isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=7)).isoformat(),
                "usage_limit": 100,
                "usage_count": 5,
                "min_cart_value": 50.0,
                "applicable_categories": [],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            },
            {
                "promo_id": "promo2",
                "name": "Promo 2",
                "type": "FIXED",
                "value": 25.0,
                "start_date": datetime.utcnow().isoformat(),
                "end_date": (datetime.utcnow() + timedelta(days=5)).isoformat(),
                "usage_limit": 50,
                "usage_count": 10,
                "min_cart_value": 100.0,
                "applicable_categories": [],
                "created_at": datetime.utcnow().isoformat(),
                "updated_at": datetime.utcnow().isoformat()
            }
        ]
        response = await client.get("/promotions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["promo_id"] == "promo1"
        assert data[1]["promo_id"] == "promo2"

@pytest.mark.asyncio
async def test_list_active_promotions_empty(client):
    with patch('app.routes.list_active_promotions', new_callable=AsyncMock) as mock_list:
        mock_list.return_value = []
        response = await client.get("/promotions")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 0
