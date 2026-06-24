import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from app.models import NotificationCreate, Notification
import uuid
from datetime import datetime

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "notification-service"

@pytest.mark.asyncio
async def test_send_notification(client):
    with patch('app.db.create_notification', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = True
        
        payload = {
            "user_id": "USER123",
            "product_id": "PROD456",
            "event_type": "added_to_cart",
            "message": "Product added to cart",
            "metadata": {"quantity": 1}
        }
        
        response = await client.post("/v1/notifications", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["user_id"] == "USER123"
        assert data["product_id"] == "PROD456"
        assert data["event_type"] == "added_to_cart"
        assert data["read"] == False
        assert "notification_id" in data
        assert "created_at" in data

@pytest.mark.asyncio
async def test_send_notification_failure(client):
    with patch('app.db.create_notification', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = False
        
        payload = {
            "user_id": "USER123",
            "product_id": "PROD456",
            "event_type": "purchase",
            "message": "Purchase confirmed"
        }
        
        response = await client.post("/v1/notifications", json=payload)
        assert response.status_code == 500
        assert "Failed to create notification" in response.json()["detail"]

@pytest.mark.asyncio
async def test_get_notification(client):
    notif_id = "NOTIF#test-123"
    notification_data = {
        "notification_id": notif_id,
        "user_id": "USER123",
        "product_id": "PROD456",
        "event_type": "stock_alert",
        "message": "Product back in stock",
        "metadata": {},
        "created_at": datetime.utcnow().isoformat(),
        "read": False
    }
    
    with patch('app.db.get_notification', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = notification_data
        
        response = await client.get(f"/v1/notifications/{notif_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["notification_id"] == notif_id
        assert data["user_id"] == "USER123"
        assert data["read"] == False

@pytest.mark.asyncio
async def test_get_notification_not_found(client):
    with patch('app.db.get_notification', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        response = await client.get("/v1/notifications/NOTIF#nonexistent")
        assert response.status_code == 404
        assert "Notification not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_list_notifications(client):
    user_id = "USER123"
    notifications = [
        {
            "notification_id": "NOTIF#1",
            "user_id": user_id,
            "product_id": "PROD1",
            "event_type": "added_to_cart",
            "message": "Added",
            "metadata": {},
            "created_at": datetime.utcnow().isoformat(),
            "read": False
        },
        {
            "notification_id": "NOTIF#2",
            "user_id": user_id,
            "product_id": "PROD2",
            "event_type": "purchase",
            "message": "Purchased",
            "metadata": {},
            "created_at": datetime.utcnow().isoformat(),
            "read": True
        }
    ]
    
    with patch('app.db.list_user_notifications', new_callable=AsyncMock) as mock_list:
        mock_list.return_value = notifications
        
        response = await client.get(f"/v1/notifications/user/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["notifications"]) == 2
        assert data["notifications"][0]["notification_id"] == "NOTIF#1"
        assert data["notifications"][1]["read"] == True

@pytest.mark.asyncio
async def test_list_notifications_with_filters(client):
    user_id = "USER123"
    unread_only_notifications = [
        {
            "notification_id": "NOTIF#1",
            "user_id": user_id,
            "product_id": "PROD1",
            "event_type": "added_to_cart",
            "message": "Added",
            "metadata": {},
            "created_at": datetime.utcnow().isoformat(),
            "read": False
        }
    ]
    
    with patch('app.db.list_user_notifications', new_callable=AsyncMock) as mock_list:
        mock_list.return_value = unread_only_notifications
        
        response = await client.get(
            f"/v1/notifications/user/{user_id}?limit=5&unread_only=true"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 1
        assert data["notifications"][0]["read"] == False
        mock_list.assert_called_once_with(user_id, limit=5, unread_only=True)

@pytest.mark.asyncio
async def test_update_notification_read_status(client):
    notif_id = "NOTIF#test-123"
    updated_data = {
        "notification_id": notif_id,
        "user_id": "USER123",
        "product_id": "PROD456",
        "event_type": "added_to_cart",
        "message": "Added to cart",
        "metadata": {},
        "created_at": datetime.utcnow().isoformat(),
        "read": True
    }
    
    with patch('app.db.update_notification', new_callable=AsyncMock) as mock_update, \
         patch('app.db.get_notification', new_callable=AsyncMock) as mock_get:
        mock_update.return_value = True
        mock_get.return_value = updated_data
        
        response = await client.patch(
            f"/v1/notifications/{notif_id}",
            json={"read": True}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["read"] == True
        mock_update.assert_called_once_with(notif_id, {"read": True})

@pytest.mark.asyncio
async def test_update_notification_not_found(client):
    with patch('app.db.update_notification', new_callable=AsyncMock) as mock_update:
        mock_update.return_value = False
        
        response = await client.patch(
            "/v1/notifications/NOTIF#nonexistent",
            json={"read": True}
        )
        assert response.status_code == 404
        assert "Notification not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_delete_notification(client):
    notif_id = "NOTIF#test-123"
    
    with patch('app.db.delete_notification', new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = True
        
        response = await client.delete(f"/v1/notifications/{notif_id}")
        assert response.status_code == 204
        mock_delete.assert_called_once_with(notif_id)

@pytest.mark.asyncio
async def test_delete_notification_not_found(client):
    with patch('app.db.delete_notification', new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = False
        
        response = await client.delete("/v1/notifications/NOTIF#nonexistent")
        assert response.status_code == 404
        assert "Notification not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_send_notification_without_metadata(client):
    with patch('app.db.create_notification', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = True
        
        payload = {
            "user_id": "USER123",
            "product_id": "PROD456",
            "event_type": "purchase",
            "message": "Order confirmed"
        }
        
        response = await client.post("/v1/notifications", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert "metadata" in data
