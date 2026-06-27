import pytest
from httpx import AsyncClient
from unittest.mock import patch, MagicMock
from app.main import app


@pytest.mark.asyncio
async def test_similar_products_happy_path():
    """
    Test successful retrieval of similar products.
    """
    mock_product = {
        "PK": "PRODUCT#PROD-12345",
        "SK": "METADATA",
        "id": "PROD-12345",
        "name": "Red Cotton T-Shirt",
        "category": "clothing",
        "price": 29.99,
        "image_url": "https://cdn.retailplatform.co.uk/images/PROD-12345.jpg",
        "rating": {"average_rating": 4.5, "rating_count": 120}
    }

    mock_similar = [
        {
            "PK": "PRODUCT#PROD-12346",
            "SK": "METADATA",
            "id": "PROD-12346",
            "name": "Blue Cotton T-Shirt",
            "category": "clothing",
            "price": 24.99,
            "image_url": "https://cdn.retailplatform.co.uk/images/PROD-12346.jpg",
            "rating": {"average_rating": 4.7, "rating_count": 95}
        },
        {
            "PK": "PRODUCT#PROD-12347",
            "SK": "METADATA",
            "id": "PROD-12347",
            "name": "Green Cotton T-Shirt",
            "category": "clothing",
            "price": 26.99,
            "image_url": "https://cdn.retailplatform.co.uk/images/PROD-12347.jpg",
            "rating": {"average_rating": 4.2, "rating_count": 60}
        }
    ]

    with patch("app.db.get_product_by_id") as mock_get_product, \
         patch("app.db.get_similar_products") as mock_get_similar:
        mock_get_product.return_value = mock_product
        mock_get_similar.return_value = mock_similar

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/PROD-12345")
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == "PROD-12345"
            assert len(data["similar_products"]) == 2
            assert data["count"] == 2
            assert data["similar_products"][0]["product_id"] == "PROD-12346"
            assert data["similar_products"][0]["name"] == "Blue Cotton T-Shirt"
            assert data["similar_products"][0]["price"] == 24.99
            assert data["similar_products"][0]["rating"] == 4.7


@pytest.mark.asyncio
async def test_similar_products_product_not_found():
    """
    Test when product_id does not exist.
    Should return 200 with empty similar_products array.
    """
    with patch("app.db.get_product_by_id") as mock_get_product:
        mock_get_product.return_value = None

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/NONEXISTENT")
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == "NONEXISTENT"
            assert data["similar_products"] == []
            assert data["count"] == 0


@pytest.mark.asyncio
async def test_similar_products_empty_category():
    """
    Test when product has no category.
    Should return 200 with empty similar_products array.
    """
    mock_product = {
        "PK": "PRODUCT#PROD-12345",
        "SK": "METADATA",
        "id": "PROD-12345",
        "name": "Unknown Product"
    }

    with patch("app.db.get_product_by_id") as mock_get_product:
        mock_get_product.return_value = mock_product

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/PROD-12345")
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == "PROD-12345"
            assert data["similar_products"] == []
            assert data["count"] == 0


@pytest.mark.asyncio
async def test_similar_products_no_matches_in_category():
    """
    Test when no other products exist in the same category.
    Should return 200 with empty similar_products array.
    """
    mock_product = {
        "PK": "PRODUCT#PROD-12345",
        "SK": "METADATA",
        "id": "PROD-12345",
        "name": "Unique Product",
        "category": "unique-category",
        "price": 99.99,
        "image_url": "https://cdn.retailplatform.co.uk/images/PROD-12345.jpg",
        "rating": {"average_rating": 5.0, "rating_count": 1}
    }

    with patch("app.db.get_product_by_id") as mock_get_product, \
         patch("app.db.get_similar_products") as mock_get_similar:
        mock_get_product.return_value = mock_product
        mock_get_similar.return_value = []

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/PROD-12345")
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == "PROD-12345"
            assert data["similar_products"] == []
            assert data["count"] == 0


@pytest.mark.asyncio
async def test_similar_products_max_4_returned():
    """
    Test that at most 4 similar products are returned.
    """
    mock_product = {
        "PK": "PRODUCT#PROD-1",
        "SK": "METADATA",
        "id": "PROD-1",
        "name": "Product 1",
        "category": "test-category",
        "price": 10.0,
        "image_url": "https://example.com/1.jpg",
        "rating": {"average_rating": 3.0, "rating_count": 10}
    }

    mock_similar = [
        {
            "id": f"PROD-{i}",
            "name": f"Product {i}",
            "category": "test-category",
            "price": float(10 + i),
            "image_url": f"https://example.com/{i}.jpg",
            "rating": {"average_rating": float(4.0 - i * 0.1), "rating_count": 50}
        }
        for i in range(2, 8)
    ]

    with patch("app.db.get_product_by_id") as mock_get_product, \
         patch("app.db.get_similar_products") as mock_get_similar:
        mock_get_product.return_value = mock_product
        mock_get_similar.return_value = mock_similar

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/v1/similar/PROD-1")
            assert response.status_code == 200
            data = response.json()
            assert len(data["similar_products"]) == 4
            assert data["count"] == 4


@pytest.mark.asyncio
async def test_health_endpoint():
    """
    Test the health check endpoint.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "similar-products-service"
