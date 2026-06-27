import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
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
        "PK": "PRODUCT#1",
        "SK": "METADATA",
        "product_id": "1",
        "name": "Test Product",
        "category": "electronics",
        "price": 99.99,
        "image_url": "https://example.com/image1.jpg",
        "rating_rate": 4.5
    }
    
    mock_similar = [
        {
            "PK": "PRODUCT#2",
            "SK": "METADATA",
            "product_id": "2",
            "name": "Similar Product 1",
            "category": "electronics",
            "price": 89.99,
            "image_url": "https://example.com/image2.jpg",
            "rating_rate": 4.7
        },
        {
            "PK": "PRODUCT#3",
            "SK": "METADATA",
            "product_id": "3",
            "name": "Similar Product 2",
            "category": "electronics",
            "price": 79.99,
            "image_url": "https://example.com/image3.jpg",
            "rating_rate": 4.2
        }
    ]
    
    with patch("app.db.table.get_item") as mock_get, \
         patch("app.db.table.query") as mock_query:
        mock_get.return_value = {"Item": mock_product}
        mock_query.return_value = {"Items": mock_similar}
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/1")
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == "1"
            assert len(data["similar_products"]) == 2
            assert data["count"] == 2
            assert data["similar_products"][0]["product_id"] == "2"
            assert data["similar_products"][0]["name"] == "Similar Product 1"
            assert data["similar_products"][0]["price"] == 89.99
            assert data["similar_products"][0]["rating_rate"] == 4.7


@pytest.mark.asyncio
async def test_similar_products_not_found():
    with patch("app.db.table.get_item") as mock_get:
        mock_get.return_value = {}
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/999")
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == "999"
            assert data["similar_products"] == []
            assert data["count"] == 0


@pytest.mark.asyncio
async def test_similar_products_empty_results():
    mock_product = {
        "PK": "PRODUCT#1",
        "SK": "METADATA",
        "product_id": "1",
        "name": "Test Product",
        "category": "electronics",
        "price": 99.99,
        "image_url": "https://example.com/image1.jpg",
        "rating_rate": 4.5
    }
    
    with patch("app.db.table.get_item") as mock_get, \
         patch("app.db.table.query") as mock_query:
        mock_get.return_value = {"Item": mock_product}
        mock_query.return_value = {"Items": []}
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/1")
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == "1"
            assert data["similar_products"] == []
            assert data["count"] == 0


@pytest.mark.asyncio
async def test_similar_products_sorted_by_rating():
    mock_product = {
        "PK": "PRODUCT#1",
        "SK": "METADATA",
        "product_id": "1",
        "name": "Test Product",
        "category": "electronics"
    }
    
    mock_similar = [
        {
            "product_id": "2",
            "name": "Lower Rating",
            "price": 50.0,
            "image_url": "https://example.com/2.jpg",
            "rating_rate": 3.5
        },
        {
            "product_id": "3",
            "name": "Highest Rating",
            "price": 60.0,
            "image_url": "https://example.com/3.jpg",
            "rating_rate": 4.9
        },
        {
            "product_id": "4",
            "name": "Medium Rating",
            "price": 55.0,
            "image_url": "https://example.com/4.jpg",
            "rating_rate": 4.0
        }
    ]
    
    with patch("app.db.table.get_item") as mock_get, \
         patch("app.db.table.query") as mock_query:
        mock_get.return_value = {"Item": mock_product}
        mock_query.return_value = {"Items": mock_similar}
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/1")
            assert response.status_code == 200
            data = response.json()
            assert data["similar_products"][0]["product_id"] == "3"
            assert data["similar_products"][0]["rating_rate"] == 4.9
            assert data["similar_products"][1]["product_id"] == "4"
            assert data["similar_products"][2]["product_id"] == "2"


@pytest.mark.asyncio
async def test_similar_products_max_4_items():
    mock_product = {
        "PK": "PRODUCT#1",
        "SK": "METADATA",
        "product_id": "1",
        "name": "Test Product",
        "category": "electronics"
    }
    
    mock_similar = [
        {"product_id": str(i), "name": f"Product {i}", "price": float(i * 10), "image_url": f"https://example.com/{i}.jpg", "rating_rate": 4.5 - (i * 0.1)}
        for i in range(2, 8)
    ]
    
    with patch("app.db.table.get_item") as mock_get, \
         patch("app.db.table.query") as mock_query:
        mock_get.return_value = {"Item": mock_product}
        mock_query.return_value = {"Items": mock_similar}
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/1")
            assert response.status_code == 200
            data = response.json()
            assert len(data["similar_products"]) == 4
            assert data["count"] == 4
