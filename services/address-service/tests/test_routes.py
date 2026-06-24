import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch, MagicMock
from app.main import app
from app.models import Address, AddressResponse
from datetime import datetime
import uuid

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_address():
    return Address(
        address_id="addr-123",
        user_id="user-456",
        street="123 Main St",
        city="New York",
        state="NY",
        postal_code="10001",
        country="USA",
        is_default=True,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

@pytest.mark.asyncio
async def test_health(client):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "address-service"

@pytest.mark.asyncio
async def test_create_address(client, sample_address):
    with patch('app.db.create_address', new_callable=AsyncMock) as mock_create:
        mock_create.return_value = sample_address
        
        response = await client.post(
            "/v1/addresses/?user_id=user-456",
            json={
                "street": "123 Main St",
                "city": "New York",
                "state": "NY",
                "postal_code": "10001",
                "country": "USA",
                "is_default": True
            }
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data["address_id"] is not None
        assert data["user_id"] == "user-456"
        assert data["street"] == "123 Main St"
        assert data["city"] == "New York"
        assert data["is_default"] is True

@pytest.mark.asyncio
async def test_get_address(client, sample_address):
    with patch('app.db.get_address', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = sample_address
        
        response = await client.get(
            "/v1/addresses/addr-123?user_id=user-456"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["address_id"] == "addr-123"
        assert data["user_id"] == "user-456"
        assert data["street"] == "123 Main St"

@pytest.mark.asyncio
async def test_get_address_not_found(client):
    with patch('app.db.get_address', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        response = await client.get(
            "/v1/addresses/nonexistent?user_id=user-456"
        )
        
        assert response.status_code == 404
        assert "Address not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_list_addresses(client, sample_address):
    addresses = [sample_address, sample_address]
    
    with patch('app.db.list_addresses', new_callable=AsyncMock) as mock_list:
        mock_list.return_value = addresses
        
        response = await client.get("/v1/addresses/?user_id=user-456")
        
        assert response.status_code == 200
        data = response.json()
        assert data["count"] == 2
        assert len(data["addresses"]) == 2
        assert data["addresses"][0]["street"] == "123 Main St"

@pytest.mark.asyncio
async def test_update_address(client, sample_address):
    updated_address = sample_address.model_copy()
    updated_address.street = "456 Park Ave"
    
    with patch('app.db.get_address', new_callable=AsyncMock) as mock_get:
        with patch('app.db.update_address', new_callable=AsyncMock) as mock_update:
            mock_get.return_value = sample_address
            mock_update.return_value = updated_address
            
            response = await client.put(
                "/v1/addresses/addr-123?user_id=user-456",
                json={"street": "456 Park Ave"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["street"] == "456 Park Ave"

@pytest.mark.asyncio
async def test_update_address_not_found(client):
    with patch('app.db.get_address', new_callable=AsyncMock) as mock_get:
        mock_get.return_value = None
        
        response = await client.put(
            "/v1/addresses/nonexistent?user_id=user-456",
            json={"street": "456 Park Ave"}
        )
        
        assert response.status_code == 404

@pytest.mark.asyncio
async def test_delete_address(client):
    with patch('app.db.delete_address', new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = True
        
        response = await client.delete(
            "/v1/addresses/addr-123?user_id=user-456"
        )
        
        assert response.status_code == 204

@pytest.mark.asyncio
async def test_delete_address_not_found(client):
    with patch('app.db.delete_address', new_callable=AsyncMock) as mock_delete:
        mock_delete.return_value = False
        
        response = await client.delete(
            "/v1/addresses/nonexistent?user_id=user-456"
        )
        
        assert response.status_code == 404
