import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "similar-products-service"}

@pytest.mark.asyncio
async def test_get_similar_products_happy_path():
    mock_product = {
        "id": "11",
        "name": "Test Product",
        "category": "electronics",
        "price": 100.0,
        "image_url": "https://example.com/11.jpg",
        "rating_rate": 4.5
    }
    
    mock_similar = [
        {
            "id": "9",
            "name": "WD 2TB Elements",
            "price": 64.0,
            "image_url": "https://dfa35pzjkre3c.cloudfront.net/images/9.jpg",
            "rating_rate": 3.3,
            "category": "electronics"
        },
        {
            "id": "10",
            "name": "Seagate Barracuda",
            "price": 89.0,
            "image_url": "https://dfa35pzjkre3c.cloudfront.net/images/10.jpg",
            "rating_rate": 4.0,
            "category": "electronics"
        }
    ]
    
    with patch("app.db.get_product_by_id", return_value=mock_product):
        with patch("app.db.query_products_by_category", return_value=mock_similar):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/v1/similar/11")
                assert response.status_code == 200
                data = response.json()
                assert data["product_id"] == "11"
                assert data["count"] == 2
                assert len(data["similar_products"]) == 2
                assert data["similar_products"][0]["product_id"] == "9"
                assert data["similar_products"][0]["price"] == 64.0
                assert isinstance(data["similar_products"][0]["rating_rate"], float)

@pytest.mark.asyncio
async def test_get_similar_products_not_found():
    with patch("app.db.get_product_by_id", return_value=None):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/999")
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == "999"
            assert data["count"] == 0
            assert data["similar_products"] == []

@pytest.mark.asyncio
async def test_get_similar_products_no_category():
    mock_product = {
        "id": "11",
        "name": "Test Product",
        "category": ""
    }
    
    with patch("app.db.get_product_by_id", return_value=mock_product):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/11")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 0
            assert data["similar_products"] == []

@pytest.mark.asyncio
async def test_get_similar_products_empty_results():
    mock_product = {
        "id": "11",
        "name": "Test Product",
        "category": "electronics"
    }
    
    with patch("app.db.get_product_by_id", return_value=mock_product):
        with patch("app.db.query_products_by_category", return_value=[]):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/v1/similar/11")
                assert response.status_code == 200
                data = response.json()
                assert data["count"] == 0
                assert data["similar_products"] == []

@pytest.mark.asyncio
async def test_get_similar_products_max_four():
    mock_product = {
        "id": "11",
        "name": "Test Product",
        "category": "electronics"
    }
    
    mock_similar = [
        {"id": f"{i}", "name": f"Product {i}", "price": float(i*10), "image_url": f"https://example.com/{i}.jpg", "rating_rate": 3.5}
        for i in range(1, 7)
    ]
    
    with patch("app.db.get_product_by_id", return_value=mock_product):
        with patch("app.db.query_products_by_category", return_value=mock_similar):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/v1/similar/11")
                assert response.status_code == 200
                data = response.json()
                assert data["count"] == 4
                assert len(data["similar_products"]) == 4
