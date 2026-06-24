import pytest
from httpx import AsyncClient
from app.main import app
from app.models import NotificationCreate, NotificationUpdate
from unittest.mock import patch, AsyncMock
import uuid

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
    assert data["service"] == "notification-service"

@pytest.mark.asyncio
@patch("app.db.create_notification")
async def test_create_notification(mock_create, client):
    mock_notification = {
        "notification_id": "NOTIF#test-id",
        "user_id": "USER#123",
        "product_id": "PROD#456",
        "notification_type": "stock_update",
        "message": "Product back in stock",
        "read": False,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }
    mock_create.return_value = mock_notification
    
    payload = {
        "user_id": "USER#123",
        "product_id": "PROD#456",
        "notification_type": "stock_update",
        "message": "Product back in stock"
    }
    
    response = await client.post("/v1/notifications/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["notification_type"] == "stock_update"
    assert data["message"] == "Product back in stock"
    mock_create.assert_called_once()

@pytest.mark.asyncio
@patch("app.db.get_notification")
async def test_get_notification(mock_get, client):
    mock_notification = {
        "notification_id": "NOTIF#test-id",
        "user_id": "USER#123",
        "product_id": "PROD#456",
        "notification_type": "stock_update",
        "message": "Product back in stock",
        "read": False,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T00:00:00"
    }
    mock_get.return_value = mock_notification
    
    response = await client.get("/v1/notifications/NOTIF#test-id")
    assert response.status_code == 200
    data = response.json()
    assert data["notification_id"] == "NOTIF#test-id"
    mock_get.assert_called_once()

@pytest.mark.asyncio
@patch("app.db.get_notification")
async def test_get_notification_not_found(mock_get, client):
    mock_get.return_value = None
    
    response = await client.get("/v1/notifications/NOTIF#nonexistent")
    assert response.status_code == 404

@pytest.mark.asyncio
@patch("app.db.get_user_notifications")
async def test_get_user_notifications(mock_get_user, client):
    mock_notifications = [
        {
            "notification_id": "NOTIF#1",
            "user_id": "USER#123",
            "product_id": "PROD#456",
            "notification_type": "stock_update",
            "message": "Product back in stock",
            "read": False,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00"
        }
    ]
    mock_get_user.return_value = (mock_notifications, 1)
    
    response = await client.get("/v1/notifications/user/USER#123")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 1
    assert len(data["notifications"]) == 1
    mock_get_user.assert_called_once()

@pytest.mark.asyncio
@patch("app.db.update_notification")
async def test_update_notification(mock_update, client):
    mock_notification = {
        "notification_id": "NOTIF#test-id",
        "user_id": "USER#123",
        "product_id": "PROD#456",
        "notification_type": "stock_update",
        "message": "Updated message",
        "read": True,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T01:00:00"
    }
    mock_update.return_value = mock_notification
    
    payload = {"read": True, "message": "Updated message"}
    response = await client.patch("/v1/notifications/NOTIF#test-id", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["read"] is True
    assert data["message"] == "Updated message"
    mock_update.assert_called_once()

@pytest.mark.asyncio
@patch("app.db.mark_as_read")
async def test_mark_notification_as_read(mock_mark, client):
    mock_notification = {
        "notification_id": "NOTIF#test-id",
        "user_id": "USER#123",
        "product_id": "PROD#456",
        "notification_type": "stock_update",
        "message": "Product back in stock",
        "read": True,
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-01T01:00:00"
    }
    mock_mark.return_value = mock_notification
    
    response = await client.put("/v1/notifications/NOTIF#test-id/read")
    assert response.status_code == 200
    data = response.json()
    assert data["read"] is True
    mock_mark.assert_called_once()

@pytest.mark.asyncio
@patch("app.db.delete_notification")
async def test_delete_notification(mock_delete, client):
    mock_delete.return_value = True
    
    response = await client.delete("/v1/notifications/NOTIF#test-id")
    assert response.status_code == 204
    mock_delete.assert_called_once()

@pytest.mark.asyncio
@patch("app.db.delete_notification")
async def test_delete_notification_not_found(mock_delete, client):
    mock_delete.return_value = False
    
    response = await client.delete("/v1/notifications/NOTIF#nonexistent")
    assert response.status_code == 404

@pytest.mark.asyncio
@patch("app.db.get_unread_count")
async def test_get_unread_count(mock_count, client):
    mock_count.return_value = 3
    
    response = await client.get("/v1/notifications/user/USER#123/unread-count")
    assert response.status_code == 200
    data = response.json()
    assert data["unread_count"] == 3
    assert data["user_id"] == "USER#123"
    mock_count.assert_called_once()

@pytest.mark.asyncio
async def test_handle_product_event(client):
    payload = {
        "product_id": "PROD#456",
        "product_name": "Test Product",
        "event_type": "stock",
        "current_value": "50 units"
    }
    
    response = await client.post("/v1/notifications/product-event", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "processed"
    assert data["event_type"] == "stock"
    assert data["product_id"] == "PROD#456"
