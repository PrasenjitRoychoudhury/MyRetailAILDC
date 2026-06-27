import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch
from app.main import app

@pytest.mark.asyncio
async def test_health_endpoint():
    """Test GET /health returns healthy status."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "service": "similar-products-service"}

@pytest.mark.asyncio
async def test_similar_products_happy_path():
    """Test GET /v1/similar/{product_id} with valid product and similar items."""
    mock_product = {
        "product_id": "11",
        "name": "Test Product",
        "category": "electronics",
        "price": 100.0,
        "image_url": "https://example.com/test.jpg",
        "rating_rate": 4.5,
        "rating_count": 10
    }
    mock_similar = [
        {
            "product_id": "12",
            "name": "WD 4TB Gaming Drive",
            "category": "electronics",
            "price": 114.0,
            "image_url": "https://dfa35pzjkre3c.cloudfront.net/images/12.jpg",
            "rating_rate": 4.8,
            "rating_count": 150
        },
        {
            "product_id": "13",
            "name": "Another Product",
            "category": "electronics",
            "price": 95.0,
            "image_url": "https://example.com/product13.jpg",
            "rating_rate": 4.2,
            "rating_count": 80
        }
    ]
    
    with patch("app.db.get_product", new_callable=AsyncMock) as mock_get, \
         patch("app.db.query_similar_products", new_callable=AsyncMock) as mock_query:
        mock_get.return_value = mock_product
        mock_query.return_value = mock_similar
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/11")
        
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == "11"
        assert len(data["similar_products"]) == 2
        assert data["count"] == 2
        assert data["similar_products"][0]["product_id"] == "12"
        assert data["similar_products"][0]["price"] == 114.0
        assert data["similar_products"][0]["rating_rate"] == 4.8

@pytest.mark.asyncio
async def test_similar_products_product_not_found():
    """Test GET /v1/similar/{product_id} when product does not exist."""
    with patch("app.db.get_product", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/nonexistent")
        
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == "nonexistent"
        assert data["similar_products"] == []
        assert data["count"] == 0

@pytest.mark.asyncio
async def test_similar_products_no_category():
    """Test GET /v1/similar/{product_id} when product has no category."""
    mock_product = {
        "product_id": "11",
        "name": "Test Product",
        "price": 100.0,
        "image_url": "https://example.com/test.jpg"
    }
    
    with patch("app.db.get_product", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_product
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/11")
        
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == "11"
        assert data["similar_products"] == []
        assert data["count"] == 0

@pytest.mark.asyncio
async def test_similar_products_empty_results():
    """Test GET /v1/similar/{product_id} when no similar products exist."""
    mock_product = {
        "product_id": "11",
        "name": "Test Product",
        "category": "electronics",
        "price": 100.0,
        "image_url": "https://example.com/test.jpg",
        "rating_rate": 4.5
    }
    
    with patch("app.db.get_product", new_callable=AsyncMock) as mock_get, \
         patch("app.db.query_similar_products", new_callable=AsyncMock) as mock_query:
        mock_get.return_value = mock_product
        mock_query.return_value = []
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/11")
        
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == "11"
        assert data["similar_products"] == []
        assert data["count"] == 0

@pytest.mark.asyncio
async def test_similar_products_max_four_items():
    """Test GET /v1/similar/{product_id} returns max 4 items."""
    mock_product = {
        "product_id": "11",
        "name": "Test Product",
        "category": "electronics",
        "price": 100.0
    }
    mock_similar = [
        {"product_id": f"{i}", "name": f"Product {i}", "category": "electronics", "price": 100.0 + i, "image_url": "https://example.com/test.jpg", "rating_rate": 5.0 - (i * 0.1)}
        for i in range(12, 17)
    ]
    
    with patch("app.db.get_product", new_callable=AsyncMock) as mock_get, \
         patch("app.db.query_similar_products", new_callable=AsyncMock) as mock_query:
        mock_get.return_value = mock_product
        mock_query.return_value = mock_similar
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/11")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["similar_products"]) == 4
        assert data["count"] == 4
