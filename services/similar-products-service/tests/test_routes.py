import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from app.main import app

@pytest.mark.asyncio
async def test_get_similar_products_happy_path():
    """Test retrieval of similar products with valid product_id."""
    mock_product = {
        "product_id": "11",
        "name": "Test Product",
        "category": "electronics",
        "price": 100.0
    }
    
    mock_similar = [
        {
            "product_id": "9",
            "name": "WD 2TB Elements",
            "price": 64.0,
            "image_url": "https://dfa35pzjkre3c.cloudfront.net/images/9.jpg",
            "rating_rate": 3.3
        },
        {
            "product_id": "10",
            "name": "Samsung 970",
            "price": 120.0,
            "image_url": "https://dfa35pzjkre3c.cloudfront.net/images/10.jpg",
            "rating_rate": 4.5
        }
    ]
    
    with patch("app.db.get_product", return_value=mock_product), \
         patch("app.db.query_similar_products", return_value=mock_similar):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/11")
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == "11"
            assert data["count"] == 2
            assert len(data["similar_products"]) == 2
            assert data["similar_products"][0]["product_id"] == "9"
            assert data["similar_products"][0]["price"] == 64.0
            assert data["similar_products"][0]["rating_rate"] == 3.3

@pytest.mark.asyncio
async def test_get_similar_products_product_not_found():
    """Test retrieval when product_id does not exist."""
    with patch("app.db.get_product", return_value=None):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/nonexistent")
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == "nonexistent"
            assert data["count"] == 0
            assert data["similar_products"] == []

@pytest.mark.asyncio
async def test_get_similar_products_empty_results():
    """Test retrieval when no similar products are found."""
    mock_product = {
        "product_id": "11",
        "name": "Test Product",
        "category": "electronics",
        "price": 100.0
    }
    
    with patch("app.db.get_product", return_value=mock_product), \
         patch("app.db.query_similar_products", return_value=[]):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/11")
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == "11"
            assert data["count"] == 0
            assert data["similar_products"] == []

@pytest.mark.asyncio
async def test_get_similar_products_max_4_items():
    """Test that at most 4 similar products are returned."""
    mock_product = {
        "product_id": "11",
        "name": "Test Product",
        "category": "electronics",
        "price": 100.0
    }
    
    mock_similar = [
        {"product_id": f"{i}", "name": f"Product {i}", "price": float(i*10), "image_url": f"url{i}", "rating_rate": 4.0}
        for i in range(1, 7)
    ]
    
    with patch("app.db.get_product", return_value=mock_product), \
         patch("app.db.query_similar_products", return_value=mock_similar):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/11")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 4
            assert len(data["similar_products"]) == 4

@pytest.mark.asyncio
async def test_health_endpoint():
    """Test the health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "similar-products-service"
