import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from app.main import app

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "similar-products-service"}

@pytest.mark.asyncio
async def test_get_similar_products_success():
    mock_product = {
        "PK": "PRODUCT#11",
        "SK": "METADATA",
        "product_id": "11",
        "name": "Samsung 49-Inch",
        "category": "electronics",
        "price": 999.99,
        "image_url": "https://example.com/11.jpg",
        "rating_rate": 4.5,
        "rating_count": 100
    }
    
    mock_similar = [
        {
            "PK": "PRODUCT#9",
            "SK": "METADATA",
            "product_id": "9",
            "name": "WD 2TB Elements",
            "category": "electronics",
            "price": 64.0,
            "image_url": "https://dfa35pzjkre3c.cloudfront.net/images/9.jpg",
            "rating_rate": 3.3,
            "rating_count": 203
        }
    ]
    
    with patch("app.db.get_product", return_value=mock_product):
        with patch("app.db.query_similar_products", return_value=mock_similar):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/v1/similar/11")
                assert response.status_code == 200
                data = response.json()
                assert data["product_id"] == "11"
                assert data["count"] == 1
                assert len(data["similar_products"]) == 1
                assert data["similar_products"][0]["product_id"] == "9"
                assert data["similar_products"][0]["price"] == 64.0
                assert data["similar_products"][0]["rating_rate"] == 3.3

@pytest.mark.asyncio
async def test_get_similar_products_not_found():
    with patch("app.db.get_product", return_value=None):
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
        "PK": "PRODUCT#5",
        "SK": "METADATA",
        "product_id": "5",
        "name": "Product without category"
    }
    
    with patch("app.db.get_product", return_value=mock_product):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/5")
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == "5"
            assert data["count"] == 0
            assert data["similar_products"] == []

@pytest.mark.asyncio
async def test_get_similar_products_empty_results():
    mock_product = {
        "PK": "PRODUCT#7",
        "SK": "METADATA",
        "product_id": "7",
        "name": "Unique Product",
        "category": "rare-category",
        "price": 1000.0,
        "image_url": "https://example.com/7.jpg",
        "rating_rate": 5.0,
        "rating_count": 1
    }
    
    with patch("app.db.get_product", return_value=mock_product):
        with patch("app.db.query_similar_products", return_value=[]):
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/v1/similar/7")
                assert response.status_code == 200
                data = response.json()
                assert data["product_id"] == "7"
                assert data["count"] == 0
                assert data["similar_products"] == []
