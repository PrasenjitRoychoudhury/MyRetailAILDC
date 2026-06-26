import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
import httpx


@pytest.fixture
def client():
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "similar-products-service"
    
    def test_v1_health_returns_ok(self, client):
        response = client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "similar-products-service"
        assert data["version"] == "1.0.0"


class TestSimilarProductsEndpoint:
    @patch("app.db.DynamoDBClient.get_product")
    @patch("app.db.DynamoDBClient.query_similar_products")
    def test_get_similar_products_success(self, mock_query, mock_get, client):
        mock_get.return_value = {
            "product_id": "prod-123",
            "name": "Test Product",
            "category": "electronics",
            "price": 99.99,
            "image_url": "https://example.com/image.jpg"
        }
        mock_query.return_value = [
            {
                "product_id": "prod-456",
                "name": "Similar Product 1",
                "price": 89.99,
                "image_url": "https://example.com/image1.jpg",
                "category": "electronics"
            },
            {
                "product_id": "prod-789",
                "name": "Similar Product 2",
                "price": 79.99,
                "image_url": "https://example.com/image2.jpg",
                "category": "electronics"
            }
        ]
        
        response = client.get("/v1/similar/prod-123")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["similar_products"]) == 2
        assert data["similar_products"][0]["product_id"] == "prod-456"
        assert data["similar_products"][0]["name"] == "Similar Product 1"
    
    @patch("app.db.DynamoDBClient.get_product")
    def test_get_similar_products_not_found(self, mock_get, client):
        mock_get.return_value = None
        
        response = client.get("/v1/similar/nonexistent-prod")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Product not found"
    
    @patch("app.db.DynamoDBClient.get_product")
    @patch("app.db.DynamoDBClient.query_similar_products")
    def test_get_similar_products_with_custom_limit(self, mock_query, mock_get, client):
        mock_get.return_value = {
            "product_id": "prod-123",
            "category": "electronics"
        }
        mock_query.return_value = [
            {"product_id": f"prod-{i}", "name": f"Product {i}", 
             "price": 50.0 + i, "image_url": f"https://example.com/{i}.jpg", 
             "category": "electronics"}
            for i in range(2)
        ]
        
        response = client.get("/v1/similar/prod-123?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        mock_query.assert_called_once()
        call_kwargs = mock_query.call_args[1]
        assert call_kwargs["limit"] == 2
    
    @patch("app.db.DynamoDBClient.get_product")
    @patch("app.db.DynamoDBClient.query_similar_products")
    def test_get_similar_products_empty_results(self, mock_query, mock_get, client):
        mock_get.return_value = {
            "product_id": "prod-123",
            "category": "rare-category"
        }
        mock_query.return_value = []
        
        response = client.get("/v1/similar/prod-123")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 0
        assert data["similar_products"] == []
    
    @patch("app.db.DynamoDBClient.get_product")
    def test_get_similar_products_no_category(self, mock_get, client):
        mock_get.return_value = {
            "product_id": "prod-123"
            # Missing category
        }
        
        response = client.get("/v1/similar/prod-123")
        assert response.status_code == 404
        data = response.json()
        assert data["detail"] == "Product not found"
    
    @patch("app.db.DynamoDBClient.get_product")
    @patch("app.db.DynamoDBClient.query_similar_products")
    def test_get_similar_products_max_4_by_default(self, mock_query, mock_get, client):
        mock_get.return_value = {
            "product_id": "prod-123",
            "category": "electronics"
        }
        mock_query.return_value = [
            {"product_id": f"prod-{i}", "name": f"Product {i}", 
             "price": 50.0 + i, "image_url": f"https://example.com/{i}.jpg", 
             "category": "electronics"}
            for i in range(4)
        ]
        
        response = client.get("/v1/similar/prod-123")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 4
        mock_query.assert_called_once()
        call_kwargs = mock_query.call_args[1]
        assert call_kwargs["limit"] == 4
