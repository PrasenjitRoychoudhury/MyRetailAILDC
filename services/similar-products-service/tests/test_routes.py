import pytest
from httpx import AsyncClient
from app.main import app
from unittest.mock import patch, MagicMock

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "healthy", "service": "similar-products-service"}

@pytest.mark.asyncio
async def test_get_product_success(client):
    """Test getting product details successfully."""
    mock_product = {
        "PK": "PRODUCT#P001",
        "SK": "METADATA",
        "product_id": "P001",
        "name": "Test Product",
        "description": "A test product",
        "category": "Electronics",
        "price": 99.99,
        "stock_qty": 50,
        "image_url": "https://example.com/image.jpg",
        "rating_rate": 4.5,
        "rating_count": 120
    }
    
    with patch("app.db.get_product_by_id", return_value=mock_product):
        response = await client.get("/v1/products/P001")
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == "P001"
        assert data["name"] == "Test Product"
        assert data["price"] == 99.99
        assert data["stock_qty"] == 50
        assert data["rating"]["rate"] == 4.5
        assert data["rating"]["count"] == 120

@pytest.mark.asyncio
async def test_get_product_not_found(client):
    """Test getting non-existent product."""
    with patch("app.db.get_product_by_id", return_value=None):
        response = await client.get("/v1/products/NONEXISTENT")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

@pytest.mark.asyncio
async def test_get_similar_products_success(client):
    """Test getting similar products by category."""
    mock_product = {
        "product_id": "P001",
        "name": "Test Product",
        "category": "Electronics",
        "price": 99.99
    }
    
    mock_similar = [
        {
            "product_id": "P002",
            "name": "Similar Product 1",
            "category": "Electronics",
            "price": 89.99,
            "rating_rate": 4.0,
            "rating_count": 85
        },
        {
            "product_id": "P003",
            "name": "Similar Product 2",
            "category": "Electronics",
            "price": 109.99,
            "rating_rate": 4.7,
            "rating_count": 200
        }
    ]
    
    with patch("app.db.get_product_by_id", return_value=mock_product), \
         patch("app.db.get_products_by_category", return_value=mock_similar + [mock_product]):
        response = await client.get("/v1/products/P001/similar?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == "P001"
        assert data["count"] == 2
        assert len(data["similar_products"]) == 2
        assert data["similar_products"][0]["product_id"] == "P002"
        assert data["similar_products"][1]["product_id"] == "P003"

@pytest.mark.asyncio
async def test_get_similar_products_empty(client):
    """Test getting similar products when none exist."""
    mock_product = {
        "product_id": "P001",
        "name": "Test Product",
        "category": "Unique",
        "price": 99.99
    }
    
    with patch("app.db.get_product_by_id", return_value=mock_product), \
         patch("app.db.get_products_by_category", return_value=[mock_product]):
        response = await client.get("/v1/products/P001/similar")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert len(data["similar_products"]) == 0

@pytest.mark.asyncio
async def test_get_similar_products_no_category(client):
    """Test getting similar products for product with no category."""
    mock_product = {
        "product_id": "P001",
        "name": "Test Product",
        "price": 99.99
    }
    
    with patch("app.db.get_product_by_id", return_value=mock_product):
        response = await client.get("/v1/products/P001/similar")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["similar_products"] == []

@pytest.mark.asyncio
async def test_get_similar_products_not_found(client):
    """Test getting similar products for non-existent product."""
    with patch("app.db.get_product_by_id", return_value=None):
        response = await client.get("/v1/products/NONEXISTENT/similar")
        assert response.status_code == 404
