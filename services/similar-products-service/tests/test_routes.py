import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "similar-products-service"
        assert data["version"] == "1.0.0"


@pytest.mark.asyncio
async def test_similar_products_v1_health():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "similar-products-service"


@pytest.mark.asyncio
async def test_similar_products_success():
    with patch("app.db.get_product_category") as mock_category, \
         patch("app.db.get_similar_products") as mock_similar:
        mock_category.return_value = "Electronics"
        mock_similar.return_value = [
            {
                "product_id": "prod-2",
                "name": "Product 2",
                "price": 99.99,
                "image_url": "https://example.com/prod2.jpg",
                "category": "Electronics"
            }
        ]
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/prod-1")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 1
            assert len(data["similar_products"]) == 1


@pytest.mark.asyncio
async def test_similar_products_not_found():
    with patch("app.db.get_product_category") as mock_category:
        mock_category.return_value = None
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/nonexistent-prod")
            assert response.status_code == 404
            data = response.json()
            assert data["detail"] == "Product not found"


@pytest.mark.asyncio
async def test_similar_products_empty():
    with patch("app.db.get_product_category") as mock_category, \
         patch("app.db.get_similar_products") as mock_similar:
        mock_category.return_value = "Electronics"
        mock_similar.return_value = []
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/prod-1")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 0
            assert len(data["similar_products"]) == 0


@pytest.mark.asyncio
async def test_similar_products_with_limit():
    with patch("app.db.get_product_category") as mock_category, \
         patch("app.db.get_similar_products") as mock_similar:
        mock_category.return_value = "Electronics"
        mock_similar.return_value = [
            {
                "product_id": f"prod-{i}",
                "name": f"Product {i}",
                "price": 100.0 + i,
                "image_url": f"https://example.com/prod{i}.jpg",
                "category": "Electronics"
            }
            for i in range(2)
        ]
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/prod-1?limit=2")
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 2
            mock_similar.assert_called_once_with("prod-1", "Electronics", 2)


@pytest.mark.asyncio
async def test_similar_products_limit_max_4():
    with patch("app.db.get_product_category") as mock_category, \
         patch("app.db.get_similar_products") as mock_similar:
        mock_category.return_value = "Electronics"
        mock_similar.return_value = []
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            # Test limit=4 (valid)
            response = await client.get("/v1/similar/prod-1?limit=4")
            assert response.status_code == 200
            
            # Test limit>4 (invalid)
            response = await client.get("/v1/similar/prod-1?limit=5")
            assert response.status_code == 422


@pytest.mark.asyncio
async def test_similar_products_default_limit():
    with patch("app.db.get_product_category") as mock_category, \
         patch("app.db.get_similar_products") as mock_similar:
        mock_category.return_value = "Electronics"
        mock_similar.return_value = []
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/prod-1")
            assert response.status_code == 200
            # Verify default limit of 4 is used
            mock_similar.assert_called_once_with("prod-1", "Electronics", 4)
