import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from app.main import app
from app.models import ProductDetail, RatingInfo

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
    assert data["service"] == "product-catalogue"

@pytest.mark.asyncio
async def test_get_product_detail_success(client):
    mock_product = {
        "product_id": "prod-001",
        "name": "Test Product",
        "description": "A test product description",
        "price": 99.99,
        "category": "Electronics",
        "stock_quantity": 50,
        "image_url": "https://example.com/image.jpg",
        "average_rating": 4.5,
        "rating_count": 120
    }
    
    with patch("app.db.get_product_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_product
        response = await client.get("/v1/products/prod-001")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["product_id"] == "prod-001"
        assert data["data"]["name"] == "Test Product"
        assert data["data"]["price"] == 99.99
        assert data["data"]["rating"]["average_rating"] == 4.5
        assert data["data"]["rating"]["rating_count"] == 120

@pytest.mark.asyncio
async def test_get_product_detail_not_found(client):
    with patch("app.db.get_product_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        response = await client.get("/v1/products/nonexistent-prod")
        
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_get_product_detail_db_error(client):
    with patch("app.db.get_product_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.side_effect = Exception("Database connection error")
        response = await client.get("/v1/products/prod-001")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is False
        assert "error" in data

@pytest.mark.asyncio
async def test_list_products_success(client):
    mock_products = [
        {
            "product_id": "prod-001",
            "name": "Product 1",
            "description": "Description 1",
            "price": 49.99,
            "category": "Electronics",
            "stock_quantity": 30,
            "image_url": "https://example.com/image1.jpg",
            "average_rating": 4.0,
            "rating_count": 50
        },
        {
            "product_id": "prod-002",
            "name": "Product 2",
            "description": "Description 2",
            "price": 79.99,
            "category": "Electronics",
            "stock_quantity": 20,
            "image_url": "https://example.com/image2.jpg",
            "average_rating": 4.3,
            "rating_count": 75
        }
    ]
    
    with patch("app.db.get_product_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_products
        response = await client.get("/v1/products?category=Electronics&limit=20")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 2
        assert len(data["data"]) == 2

@pytest.mark.asyncio
async def test_list_products_empty(client):
    with patch("app.db.get_product_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = []
        response = await client.get("/v1/products?limit=20")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["count"] == 0

@pytest.mark.asyncio
async def test_product_detail_with_zero_stock(client):
    mock_product = {
        "product_id": "prod-003",
        "name": "Out of Stock Product",
        "description": "This product is out of stock",
        "price": 199.99,
        "category": "Books",
        "stock_quantity": 0,
        "image_url": "https://example.com/image3.jpg",
        "average_rating": 3.8,
        "rating_count": 200
    }
    
    with patch("app.db.get_product_by_id", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_product
        response = await client.get("/v1/products/prod-003")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["stock_quantity"] == 0
