import pytest
from httpx import AsyncClient
from unittest.mock import patch, AsyncMock
from app.main import app


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_endpoint(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "similar-products-service"


@pytest.mark.asyncio
async def test_get_similar_products_with_results(client):
    mock_product = {
        "PK": "PRODUCT#PROD-12345",
        "SK": "METADATA",
        "product_id": "PROD-12345",
        "name": "Red Cotton T-Shirt Large",
        "category": "clothing",
        "price": 29.99,
        "image_url": "https://cdn.example.com/PROD-12345.jpg",
        "rating": 4.5,
        "stock_quantity": 10
    }
    
    mock_category_products = [
        {
            "PK": "PRODUCT#PROD-12345",
            "SK": "METADATA",
            "product_id": "PROD-12345",
            "name": "Red Cotton T-Shirt Large",
            "category": "clothing",
            "price": 29.99,
            "image_url": "https://cdn.example.com/PROD-12345.jpg",
            "rating": 4.5,
            "stock_quantity": 10
        },
        {
            "PK": "PRODUCT#PROD-12346",
            "SK": "METADATA",
            "product_id": "PROD-12346",
            "name": "Blue Cotton T-Shirt Medium",
            "category": "clothing",
            "price": 24.99,
            "image_url": "https://cdn.example.com/PROD-12346.jpg",
            "rating": 4.7,
            "stock_quantity": 5
        },
        {
            "PK": "PRODUCT#PROD-12347",
            "SK": "METADATA",
            "product_id": "PROD-12347",
            "name": "Green Cotton T-Shirt Small",
            "category": "clothing",
            "price": 22.99,
            "image_url": "https://cdn.example.com/PROD-12347.jpg",
            "rating": 4.2,
            "stock_quantity": 0
        }
    ]
    
    with patch("app.db.get_product", new_callable=AsyncMock) as mock_get:
        with patch("app.db.scan_products_by_category", new_callable=AsyncMock) as mock_scan:
            mock_get.return_value = mock_product
            mock_scan.return_value = mock_category_products
            
            response = await client.get("/v1/similar/PROD-12345")
            
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == "PROD-12345"
            assert data["count"] == 2
            assert len(data["similar_products"]) == 2
            assert data["similar_products"][0]["product_id"] == "PROD-12346"
            assert data["similar_products"][0]["rating"] == 4.7
            assert data["similar_products"][1]["product_id"] == "PROD-12347"
            assert data["similar_products"][1]["rating"] == 4.2


@pytest.mark.asyncio
async def test_get_similar_products_product_not_found(client):
    with patch("app.db.get_product", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        response = await client.get("/v1/similar/NONEXISTENT")
        
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == "NONEXISTENT"
        assert data["count"] == 0
        assert data["similar_products"] == []


@pytest.mark.asyncio
async def test_get_similar_products_empty_category(client):
    mock_product = {
        "PK": "PRODUCT#PROD-99999",
        "SK": "METADATA",
        "product_id": "PROD-99999",
        "name": "Unique Item",
        "category": "rare-items",
        "price": 99.99,
        "image_url": "https://cdn.example.com/PROD-99999.jpg",
        "rating": 5.0,
        "stock_quantity": 1
    }
    
    with patch("app.db.get_product", new_callable=AsyncMock) as mock_get:
        with patch("app.db.scan_products_by_category", new_callable=AsyncMock) as mock_scan:
            mock_get.return_value = mock_product
            mock_scan.return_value = [mock_product]
            
            response = await client.get("/v1/similar/PROD-99999")
            
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == "PROD-99999"
            assert data["count"] == 0
            assert data["similar_products"] == []


@pytest.mark.asyncio
async def test_get_similar_products_max_four_results(client):
    mock_product = {
        "PK": "PRODUCT#PROD-1",
        "SK": "METADATA",
        "product_id": "PROD-1",
        "name": "Product 1",
        "category": "electronics",
        "price": 100.0,
        "image_url": "https://cdn.example.com/PROD-1.jpg",
        "rating": 3.0,
        "stock_quantity": 10
    }
    
    mock_category_products = [
        {
            "product_id": f"PROD-{i}",
            "name": f"Product {i}",
            "category": "electronics",
            "price": 100.0 + i,
            "image_url": f"https://cdn.example.com/PROD-{i}.jpg",
            "rating": 5.0 - (i * 0.1),
            "stock_quantity": 10
        }
        for i in range(1, 8)
    ]
    
    with patch("app.db.get_product", new_callable=AsyncMock) as mock_get:
        with patch("app.db.scan_products_by_category", new_callable=AsyncMock) as mock_scan:
            mock_get.return_value = mock_product
            mock_scan.return_value = mock_category_products
            
            response = await client.get("/v1/similar/PROD-1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["count"] == 4
            assert len(data["similar_products"]) == 4


@pytest.mark.asyncio
async def test_get_similar_products_sorted_by_rating(client):
    mock_product = {
        "PK": "PRODUCT#PROD-A",
        "SK": "METADATA",
        "product_id": "PROD-A",
        "name": "Product A",
        "category": "books",
        "price": 15.0,
        "image_url": "https://cdn.example.com/PROD-A.jpg",
        "rating": 3.0,
        "stock_quantity": 5
    }
    
    mock_category_products = [
        {
            "product_id": "PROD-A",
            "name": "Product A",
            "category": "books",
            "price": 15.0,
            "image_url": "https://cdn.example.com/PROD-A.jpg",
            "rating": 3.0,
            "stock_quantity": 5
        },
        {
            "product_id": "PROD-B",
            "name": "Product B",
            "category": "books",
            "price": 12.0,
            "image_url": "https://cdn.example.com/PROD-B.jpg",
            "rating": 4.8,
            "stock_quantity": 10
        },
        {
            "product_id": "PROD-C",
            "name": "Product C",
            "category": "books",
            "price": 18.0,
            "image_url": "https://cdn.example.com/PROD-C.jpg",
            "rating": 4.2,
            "stock_quantity": 3
        }
    ]
    
    with patch("app.db.get_product", new_callable=AsyncMock) as mock_get:
        with patch("app.db.scan_products_by_category", new_callable=AsyncMock) as mock_scan:
            mock_get.return_value = mock_product
            mock_scan.return_value = mock_category_products
            
            response = await client.get("/v1/similar/PROD-A")
            
            assert response.status_code == 200
            data = response.json()
            assert data["similar_products"][0]["rating"] == 4.8
            assert data["similar_products"][1]["rating"] == 4.2


@pytest.mark.asyncio
async def test_get_similar_products_excludes_queried_product(client):
    mock_product = {
        "PK": "PRODUCT#PROD-100",
        "SK": "METADATA",
        "product_id": "PROD-100",
        "name": "Main Product",
        "category": "furniture",
        "price": 299.99,
        "image_url": "https://cdn.example.com/PROD-100.jpg",
        "rating": 4.0,
        "stock_quantity": 2
    }
    
    mock_category_products = [
        mock_product,
        {
            "product_id": "PROD-101",
            "name": "Similar Product 1",
            "category": "furniture",
            "price": 250.0,
            "image_url": "https://cdn.example.com/PROD-101.jpg",
            "rating": 4.5,
            "stock_quantity": 5
        }
    ]
    
    with patch("app.db.get_product", new_callable=AsyncMock) as mock_get:
        with patch("app.db.scan_products_by_category", new_callable=AsyncMock) as mock_scan:
            mock_get.return_value = mock_product
            mock_scan.return_value = mock_category_products
            
            response = await client.get("/v1/similar/PROD-100")
            
            assert response.status_code == 200
            data = response.json()
            product_ids = [p["product_id"] for p in data["similar_products"]]
            assert "PROD-100" not in product_ids
            assert "PROD-101" in product_ids


@pytest.mark.asyncio
async def test_get_similar_products_response_structure(client):
    mock_product = {
        "PK": "PRODUCT#PROD-STRUCT",
        "SK": "METADATA",
        "product_id": "PROD-STRUCT",
        "name": "Structure Test",
        "category": "test",
        "price": 50.0,
        "image_url": "https://cdn.example.com/PROD-STRUCT.jpg",
        "rating": 3.5,
        "stock_quantity": 1
    }
    
    mock_category_products = [
        mock_product,
        {
            "product_id": "PROD-STRUCT-2",
            "name": "Structure Test 2",
            "category": "test",
            "price": 55.0,
            "image_url": "https://cdn.example.com/PROD-STRUCT-2.jpg",
            "rating": 3.8,
            "stock_quantity": 2
        }
    ]
    
    with patch("app.db.get_product", new_callable=AsyncMock) as mock_get:
        with patch("app.db.scan_products_by_category", new_callable=AsyncMock) as mock_scan:
            mock_get.return_value = mock_product
            mock_scan.return_value = mock_category_products
            
            response = await client.get("/v1/similar/PROD-STRUCT")
            
            assert response.status_code == 200
            data = response.json()
            
            assert "product_id" in data
            assert "similar_products" in data
            assert "count" in data
            
            assert isinstance(data["similar_products"], list)
            assert data["count"] == len(data["similar_products"])
            
            if data["similar_products"]:
                product = data["similar_products"][0]
                assert "product_id" in product
                assert "name" in product
                assert "price" in product
                assert "image_url" in product
                assert "rating" in product
