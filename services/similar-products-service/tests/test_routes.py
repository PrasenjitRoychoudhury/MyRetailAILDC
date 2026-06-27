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


@pytest.mark.asyncio
async def test_similar_products_happy_path():
    mock_product = {
        "PK": "PRODUCT#11",
        "SK": "METADATA",
        "product_id": "11",
        "name": "Test Product",
        "category": "electronics",
        "price": 100.0,
    }
    
    mock_similar = [
        {
            "PK": "PRODUCT#9",
            "SK": "METADATA",
            "product_id": "9",
            "name": "WD 2TB Elements",
            "price": 64.0,
            "image_url": "https://dfa35pzjkre3c.cloudfront.net/images/9.jpg",
            "rating_rate": 3.3,
        },
        {
            "PK": "PRODUCT#10",
            "SK": "METADATA",
            "product_id": "10",
            "name": "Another Product",
            "price": 75.0,
            "image_url": "https://example.com/image.jpg",
            "rating_rate": 4.0,
        },
    ]
    
    with patch("app.db.get_product", new_callable=AsyncMock) as mock_get:
        with patch("app.db.query_similar_products", new_callable=AsyncMock) as mock_query:
            mock_get.return_value = mock_product
            mock_query.return_value = mock_similar
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/v1/similar/11")
                
                assert response.status_code == 200
                data = response.json()
                assert data["product_id"] == "11"
                assert data["count"] == 2
                assert len(data["similar_products"]) == 2
                
                # Check first product (price sorted ascending)
                first = data["similar_products"][0]
                assert first["product_id"] == "9"
                assert first["name"] == "WD 2TB Elements"
                assert first["price"] == 64.0
                assert first["image_url"] == "https://dfa35pzjkre3c.cloudfront.net/images/9.jpg"
                assert first["rating_rate"] == 3.3


@pytest.mark.asyncio
async def test_similar_products_not_found():
    with patch("app.db.get_product", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/999")
            
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == "999"
            assert data["count"] == 0
            assert data["similar_products"] == []


@pytest.mark.asyncio
async def test_similar_products_no_category():
    mock_product = {
        "PK": "PRODUCT#11",
        "SK": "METADATA",
        "product_id": "11",
        "name": "Test Product",
    }
    
    with patch("app.db.get_product", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_product
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/11")
            
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == "11"
            assert data["count"] == 0
            assert data["similar_products"] == []


@pytest.mark.asyncio
async def test_similar_products_empty_results():
    mock_product = {
        "PK": "PRODUCT#11",
        "SK": "METADATA",
        "product_id": "11",
        "name": "Test Product",
        "category": "electronics",
    }
    
    with patch("app.db.get_product", new_callable=AsyncMock) as mock_get:
        with patch("app.db.query_similar_products", new_callable=AsyncMock) as mock_query:
            mock_get.return_value = mock_product
            mock_query.return_value = []
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/v1/similar/11")
                
                assert response.status_code == 200
                data = response.json()
                assert data["product_id"] == "11"
                assert data["count"] == 0
                assert data["similar_products"] == []


@pytest.mark.asyncio
async def test_similar_products_max_four():
    mock_product = {
        "PK": "PRODUCT#1",
        "SK": "METADATA",
        "product_id": "1",
        "category": "electronics",
    }
    
    mock_similar = [
        {
            "product_id": str(i),
            "name": f"Product {i}",
            "price": float(50 + i * 10),
            "image_url": f"https://example.com/{i}.jpg",
            "rating_rate": 4.0,
        }
        for i in range(2, 6)
    ]
    
    with patch("app.db.get_product", new_callable=AsyncMock) as mock_get:
        with patch("app.db.query_similar_products", new_callable=AsyncMock) as mock_query:
            mock_get.return_value = mock_product
            mock_query.return_value = mock_similar
            
            async with AsyncClient(app=app, base_url="http://test") as client:
                response = await client.get("/v1/similar/1")
                
                assert response.status_code == 200
                data = response.json()
                assert data["count"] == 4
                assert len(data["similar_products"]) == 4
