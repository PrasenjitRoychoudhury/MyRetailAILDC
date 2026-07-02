import pytest
from httpx import AsyncClient
from app.main import app
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_health_endpoint():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        assert response.json() == {
            "status": "healthy",
            "service": "similar-products-service"
        }


@pytest.mark.asyncio
async def test_similar_products_happy_path():
    mock_product = {
        "product_id": "11",
        "name": "Laptop",
        "category": "Electronics",
        "price": 999.99,
        "PK": "PRODUCT#11",
        "SK": "METADATA"
    }
    
    mock_similar = [
        {
            "product_id": "9",
            "name": "WD 2TB Elements",
            "category": "Electronics",
            "price": 64.0,
            "image_url": "https://dfa35pzjkre3c.cloudfront.net/images/9.jpg",
            "rating_rate": 3.3,
            "PK": "PRODUCT#9",
            "SK": "METADATA"
        },
        {
            "product_id": "10",
            "name": "Keyboard",
            "category": "Electronics",
            "price": 49.99,
            "image_url": "https://dfa35pzjkre3c.cloudfront.net/images/10.jpg",
            "rating_rate": 4.5,
            "PK": "PRODUCT#10",
            "SK": "METADATA"
        }
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
                assert len(data["similar_products"]) == 2
                assert data["count"] == 2
                assert data["similar_products"][0]["product_id"] == "9"
                assert data["similar_products"][0]["name"] == "WD 2TB Elements"
                assert data["similar_products"][0]["price"] == 64.0
                assert data["similar_products"][0]["rating_rate"] == 3.3


@pytest.mark.asyncio
async def test_similar_products_not_found():
    with patch("app.db.get_product", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/999")
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == "999"
            assert data["similar_products"] == []
            assert data["count"] == 0


@pytest.mark.asyncio
async def test_similar_products_empty_category():
    mock_product = {
        "product_id": "11",
        "name": "Laptop",
        "category": "",
        "price": 999.99,
        "PK": "PRODUCT#11",
        "SK": "METADATA"
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
async def test_similar_products_no_results():
    mock_product = {
        "product_id": "11",
        "name": "Laptop",
        "category": "Electronics",
        "price": 999.99,
        "PK": "PRODUCT#11",
        "SK": "METADATA"
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
                assert data["similar_products"] == []
                assert data["count"] == 0


@pytest.mark.asyncio
async def test_similar_products_max_four():
    mock_product = {
        "product_id": "11",
        "name": "Laptop",
        "category": "Electronics",
        "price": 999.99,
        "PK": "PRODUCT#11",
        "SK": "METADATA"
    }
    
    mock_similar = [
        {
            "product_id": f"{i}",
            "name": f"Product {i}",
            "category": "Electronics",
            "price": float(50 + i),
            "image_url": f"https://example.com/{i}.jpg",
            "rating_rate": 4.0,
            "PK": f"PRODUCT#{i}",
            "SK": "METADATA"
        }
        for i in range(1, 7)
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
                assert len(data["similar_products"]) == 4
                assert data["count"] == 4
