import pytest
from unittest.mock import patch, MagicMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from botocore.exceptions import ClientError

BASE_URL = "http://test"

MOCK_COUPON_ITEM = {
    "PK": "COUPON#SAVE10",
    "SK": "METADATA",
    "coupon_code": "SAVE10",
    "discount_type": "percentage",
    "discount_value": 10.0,
    "min_order_value": 50.0,
    "max_uses": 100,
    "times_used": 5,
    "expiry_date": "2099-12-31T23:59:59",
    "applicable_categories": [],
    "applicable_product_ids": [],
    "active": True,
    "created_at": "2024-01-01T00:00:00+00:00",
    "updated_at": "2024-01-01T00:00:00+00:00",
}


@pytest.fixture
def mock_table():
    with patch("app.db.get_table") as mock_get_table:
        mock_tbl = MagicMock()
        mock_get_table.return_value = mock_tbl
        yield mock_tbl


@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "coupon-service"


@pytest.mark.asyncio
async def test_create_coupon_success(mock_table):
    mock_table.put_item.return_value = {}
    payload = {
        "coupon_code": "SAVE10",
        "discount_type": "percentage",
        "discount_value": 10.0,
        "min_order_value": 50.0,
        "max_uses": 100,
        "expiry_date": "2099-12-31T23:59:59",
        "applicable_categories": [],
        "applicable_product_ids": [],
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.post("/v1/coupons/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["coupon_code"] == "SAVE10"
    assert data["discount_type"] == "percentage"
    assert data["discount_value"] == 10.0
    assert data["active"] is True
    assert data["times_used"] == 0


@pytest.mark.asyncio
async def test_create_coupon_conflict(mock_table):
    error_response = {"Error": {"Code": "ConditionalCheckFailedException", "Message": ""}}
    mock_table.put_item.side_effect = ClientError(error_response, "PutItem")
    payload = {
        "coupon_code": "SAVE10",
        "discount_type": "percentage",
        "discount_value": 10.0,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.post("/v1/coupons/", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_get_coupon_success(mock_table):
    mock_table.get_item.return_value = {"Item": MOCK_COUPON_ITEM}
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.get("/v1/coupons/SAVE10")
    assert response.status_code == 200
    data = response.json()
    assert data["coupon_code"] == "SAVE10"


@pytest.mark.asyncio
async def test_get_coupon_not_found(mock_table):
    mock_table.get_item.return_value = {}
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.get("/v1/coupons/NOTEXIST")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_update_coupon_success(mock_table):
    updated_item = {**MOCK_COUPON_ITEM, "discount_value": 15.0}
    mock_table.update_item.return_value = {"Attributes": updated_item}
    payload = {"discount_value": 15.0}
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.patch("/v1/coupons/SAVE10", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["discount_value"] == 15.0


@pytest.mark.asyncio
async def test_update_coupon_not_found(mock_table):
    error_response = {"Error": {"Code": "ConditionalCheckFailedException", "Message": ""}}
    mock_table.update_item.side_effect = ClientError(error_response, "UpdateItem")
    payload = {"discount_value": 15.0}
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.patch("/v1/coupons/NOTEXIST", json=payload)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_delete_coupon_success(mock_table):
    mock_table.delete_item.return_value = {}
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.delete("/v1/coupons/SAVE10")
    assert response.status_code == 204


@pytest.mark.asyncio
async def test_delete_coupon_not_found(mock_table):
    error_response = {"Error": {"Code": "ConditionalCheckFailedException", "Message": ""}}
    mock_table.delete_item.side_effect = ClientError(error_response, "DeleteItem")
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.delete("/v1/coupons/NOTEXIST")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_validate_coupon_valid(mock_table):
    mock_table.get_item.return_value = {"Item": MOCK_COUPON_ITEM}
    payload = {
        "coupon_code": "SAVE10",
        "order_value": 100.0,
        "product_ids": [],
        "categories": [],
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.post("/v1/coupons/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["discount_amount"] == 10.0
    assert data["final_order_value"] == 90.0


@pytest.mark.asyncio
async def test_validate_coupon_below_min_order(mock_table):
    mock_table.get_item.return_value = {"Item": MOCK_COUPON_ITEM}
    payload = {
        "coupon_code": "SAVE10",
        "order_value": 20.0,
        "product_ids": [],
        "categories": [],
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.post("/v1/coupons/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "minimum" in data["message"].lower() or "least" in data["message"].lower()


@pytest.mark.asyncio
async def test_validate_coupon_inactive(mock_table):
    inactive_item = {**MOCK_COUPON_ITEM, "active": False}
    mock_table.get_item.return_value = {"Item": inactive_item}
    payload = {
        "coupon_code": "SAVE10",
        "order_value": 100.0,
        "product_ids": [],
        "categories": [],
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.post("/v1/coupons/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "inactive" in data["message"].lower()


@pytest.mark.asyncio
async def test_validate_coupon_expired(mock_table):
    expired_item = {**MOCK_COUPON_ITEM, "expiry_date": "2000-01-01T00:00:00"}
    mock_table.get_item.return_value = {"Item": expired_item}
    payload = {
        "coupon_code": "SAVE10",
        "order_value": 100.0,
        "product_ids": [],
        "categories": [],
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.post("/v1/coupons/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "expired" in data["message"].lower()


@pytest.mark.asyncio
async def test_validate_coupon_not_found(mock_table):
    mock_table.get_item.return_value = {}
    payload = {
        "coupon_code": "GHOST",
        "order_value": 100.0,
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.post("/v1/coupons/validate", json=payload)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_validate_coupon_usage_limit_reached(mock_table):
    maxed_item = {**MOCK_COUPON_ITEM, "times_used": 100, "max_uses": 100}
    mock_table.get_item.return_value = {"Item": maxed_item}
    payload = {
        "coupon_code": "SAVE10",
        "order_value": 100.0,
        "product_ids": [],
        "categories": [],
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.post("/v1/coupons/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is False
    assert "limit" in data["message"].lower()


@pytest.mark.asyncio
async def test_validate_fixed_discount(mock_table):
    fixed_item = {
        **MOCK_COUPON_ITEM,
        "discount_type": "fixed",
        "discount_value": 20.0,
        "min_order_value": 0.0,
    }
    mock_table.get_item.return_value = {"Item": fixed_item}
    payload = {
        "coupon_code": "SAVE10",
        "order_value": 80.0,
        "product_ids": [],
        "categories": [],
    }
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE_URL) as client:
        response = await client.post("/v1/coupons/validate", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["valid"] is True
    assert data["discount_amount"] == 20.0
    assert data["final_order_value"] == 60.0
