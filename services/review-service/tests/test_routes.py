import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from app.models import Review, ProductRatingSummary
from datetime import datetime

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
    assert data["service"] == "review-service"

@pytest.mark.asyncio
async def test_create_review(client):
    with patch("app.routes.db_client.create_review", new_callable=AsyncMock):
        with patch("app.routes.db_client.update_product_rating", new_callable=AsyncMock):
            review_data = {
                "product_id": "prod-123",
                "user_id": "user-456",
                "rating": 5,
                "title": "Great product",
                "content": "This product exceeded my expectations"
            }
            response = await client.post("/v1/reviews", json=review_data)
            assert response.status_code == 201
            data = response.json()
            assert data["product_id"] == "prod-123"
            assert data["user_id"] == "user-456"
            assert data["rating"] == 5
            assert data["title"] == "Great product"

@pytest.mark.asyncio
async def test_get_product_reviews(client):
    mock_summary = ProductRatingSummary(
        product_id="prod-123",
        average_rating=4.5,
        rating_count=2,
        rating_distribution={5: 1, 4: 1}
    )
    
    mock_review = Review(
        review_id="review-1",
        product_id="prod-123",
        user_id="user-456",
        rating=5,
        title="Great",
        content="Good product",
        created_at=datetime.utcnow(),
        helpful_count=10
    )
    
    with patch("app.routes.db_client.get_product_rating_summary", new_callable=AsyncMock, return_value=mock_summary):
        with patch("app.routes.db_client.get_reviews_by_product", new_callable=AsyncMock, return_value=[mock_review]):
            response = await client.get("/v1/products/prod-123/reviews")
            assert response.status_code == 200
            data = response.json()
            assert data["product_id"] == "prod-123"
            assert data["summary"]["average_rating"] == 4.5
            assert data["summary"]["rating_count"] == 2
            assert len(data["reviews"]) == 1
            assert data["total_reviews"] == 1

@pytest.mark.asyncio
async def test_get_product_rating_summary(client):
    mock_summary = ProductRatingSummary(
        product_id="prod-123",
        average_rating=4.2,
        rating_count=5,
        rating_distribution={5: 3, 4: 1, 3: 1}
    )
    
    with patch("app.routes.db_client.get_product_rating_summary", new_callable=AsyncMock, return_value=mock_summary):
        response = await client.get("/v1/products/prod-123/rating")
        assert response.status_code == 200
        data = response.json()
        assert data["product_id"] == "prod-123"
        assert data["average_rating"] == 4.2
        assert data["rating_count"] == 5

@pytest.mark.asyncio
async def test_get_review(client):
    mock_review = Review(
        review_id="review-1",
        product_id="prod-123",
        user_id="user-456",
        rating=4,
        title="Good",
        content="Nice product",
        created_at=datetime.utcnow(),
        helpful_count=5
    )
    
    with patch("app.routes.db_client.get_review", new_callable=AsyncMock, return_value=mock_review):
        response = await client.get("/v1/reviews/review-1")
        assert response.status_code == 200
        data = response.json()
        assert data["review_id"] == "review-1"
        assert data["rating"] == 4

@pytest.mark.asyncio
async def test_get_review_not_found(client):
    with patch("app.routes.db_client.get_review", new_callable=AsyncMock, return_value=None):
        response = await client.get("/v1/reviews/nonexistent")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_update_review(client):
    mock_existing = Review(
        review_id="review-1",
        product_id="prod-123",
        user_id="user-456",
        rating=3,
        title="Old",
        content="Old content",
        created_at=datetime.utcnow(),
        helpful_count=0
    )
    
    with patch("app.routes.db_client.get_review", new_callable=AsyncMock, return_value=mock_existing):
        with patch("app.routes.db_client.update_review", new_callable=AsyncMock):
            update_data = {
                "product_id": "prod-123",
                "user_id": "user-456",
                "rating": 5,
                "title": "Updated",
                "content": "Updated content"
            }
            response = await client.put("/v1/reviews/review-1", json=update_data)
            assert response.status_code == 200
            data = response.json()
            assert data["rating"] == 5
            assert data["title"] == "Updated"

@pytest.mark.asyncio
async def test_delete_review(client):
    mock_review = Review(
        review_id="review-1",
        product_id="prod-123",
        user_id="user-456",
        rating=4,
        title="Good",
        content="Nice",
        created_at=datetime.utcnow()
    )
    
    with patch("app.routes.db_client.get_review", new_callable=AsyncMock, return_value=mock_review):
        with patch("app.routes.db_client.delete_review", new_callable=AsyncMock):
            response = await client.delete("/v1/reviews/review-1")
            assert response.status_code == 204

@pytest.mark.asyncio
async def test_delete_review_not_found(client):
    with patch("app.routes.db_client.get_review", new_callable=AsyncMock, return_value=None):
        response = await client.delete("/v1/reviews/nonexistent")
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_mark_review_helpful(client):
    mock_review = Review(
        review_id="review-1",
        product_id="prod-123",
        user_id="user-456",
        rating=5,
        title="Great",
        content="Excellent",
        created_at=datetime.utcnow(),
        helpful_count=10
    )
    
    with patch("app.routes.db_client.get_review", new_callable=AsyncMock, return_value=mock_review):
        with patch("app.routes.db_client.update_review_helpful", new_callable=AsyncMock):
            response = await client.post("/v1/reviews/review-1/helpful", json={"helpful": True})
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"

@pytest.mark.asyncio
async def test_mark_review_unhelpful(client):
    mock_review = Review(
        review_id="review-1",
        product_id="prod-123",
        user_id="user-456",
        rating=2,
        title="Bad",
        content="Disappointed",
        created_at=datetime.utcnow(),
        unhelpful_count=5
    )
    
    with patch("app.routes.db_client.get_review", new_callable=AsyncMock, return_value=mock_review):
        with patch("app.routes.db_client.update_review_helpful", new_callable=AsyncMock):
            response = await client.post("/v1/reviews/review-1/helpful", json={"helpful": False})
            assert response.status_code == 200
