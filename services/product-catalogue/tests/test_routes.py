import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from app.main import app
from app.models import ProductDetail, ProductRating

@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "product-catalogue"

@pytest.mark.asyncio
async def test_get_product_success():
    mock_product = {
        "id": "PROD001",
        "name": "Test Product",
        "description": "A test product",
        "price": 99.99,
        "category": "Electronics",
        "stock_quantity": 50,
        "image_url": "https://example.com/image.jpg",
        "rating": {
            "average_rating": 4.5,
            "rating_count": 120
        }
    }
    
    with patch("app.db.get_product_by_id", new_callable=AsyncMock) as mock_db:
        mock_db.return_value = mock_product
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/products/PROD001")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert data["data"]["name"] == "Test Product"
            assert data["data"]["price"] == 99.99
            assert data["data"]["rating"]["average_rating"] == 4.5

@pytest.mark.asyncio
async def test_get_product_not_found():
    with patch("app.db.get_product_by_id", new_callable=AsyncMock) as mock_db:
        mock_db.return_value = None
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/products/NONEXISTENT")
            assert response.status_code == 404
            data = response.json()
            assert data["detail"]["success"] is False
            assert data["detail"]["error_code"] == "PRODUCT_NOT_FOUND"

@pytest.mark.asyncio
async def test_list_products_success():
    mock_products = [
        {
            "id": "PROD001",
            "name": "Product 1",
            "description": "Description 1",
            "price": 29.99,
            "category": "Electronics",
            "stock_quantity": 100,
            "image_url": "https://example.com/1.jpg",
            "rating": {"average_rating": 4.0, "rating_count": 50}
        },
        {
            "id": "PROD002",
            "name": "Product 2",
            "description": "Description 2",
            "price": 49.99,
            "category": "Electronics",
            "stock_quantity": 75,
            "image_url": "https://example.com/2.jpg",
            "rating": {"average_rating": 4.5, "rating_count": 80}
        }
    ]
    
    with patch("app.db.list_products", new_callable=AsyncMock) as mock_db:
        mock_db.return_value = (mock_products, 2)
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/products?limit=20&offset=0")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 2
            assert data["pagination"]["total"] == 2
            assert data["pagination"]["limit"] == 20
            assert data["pagination"]["offset"] == 0

@pytest.mark.asyncio
async def test_list_products_with_category_filter():
    mock_products = [
        {
            "id": "PROD001",
            "name": "Product 1",
            "description": "Description 1",
            "price": 29.99,
            "category": "Electronics",
            "stock_quantity": 100,
            "image_url": "https://example.com/1.jpg",
            "rating": {"average_rating": 4.0, "rating_count": 50}
        }
    ]
    
    with patch("app.db.list_products", new_callable=AsyncMock) as mock_db:
        mock_db.return_value = (mock_products, 1)
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/products?category=Electronics&limit=20&offset=0")
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert len(data["data"]) == 1
            mock_db.assert_called_once_with(category="Electronics", limit=20, offset=0)

@pytest.mark.asyncio
async def test_get_product_internal_error():
    with patch("app.db.get_product_by_id", new_callable=AsyncMock) as mock_db:
        mock_db.side_effect = Exception("Database connection error")
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/products/PROD001")
            assert response.status_code == 500
            data = response.json()
            assert data["detail"]["success"] is False
            assert data["detail"]["error_code"] == "INTERNAL_ERROR"

@pytest.mark.asyncio
async def test_list_products_pagination():
    mock_products = []
    
    with patch("app.db.list_products", new_callable=AsyncMock) as mock_db:
        mock_db.return_value = (mock_products, 0)
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/products?limit=50&offset=10")
            assert response.status_code == 200
            data = response.json()
            assert data["pagination"]["limit"] == 50
            assert data["pagination"]["offset"] == 10
            mock_db.assert_called_once_with(category=None, limit=50, offset=10)
