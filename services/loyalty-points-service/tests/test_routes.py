import pytest
from httpx import AsyncClient
from app.main import app
from unittest.mock import patch, MagicMock
from decimal import Decimal
import math

@pytest.mark.asyncio
async def test_health_check():
    """Test health check endpoint."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "loyalty-points"
        assert "timestamp" in data

@pytest.mark.asyncio
async def test_get_balance_success():
    """Test retrieving existing customer balance."""
    with patch("app.db.get_customer_balance") as mock_get:
        mock_get.return_value = {
            "PK": "CUSTOMER#cust-12345",
            "SK": "LOYALTY#BALANCE",
            "points_balance": 450,
            "updated_at": "2025-02-14T10:30:00Z",
        }
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/loyalty/cust-12345/balance")
            assert response.status_code == 200
            data = response.json()
            assert data["customer_id"] == "cust-12345"
            assert data["points_balance"] == 450
            assert data["as_of"] == "2025-02-14T10:30:00Z"

@pytest.mark.asyncio
async def test_get_balance_not_found():
    """Test balance inquiry for non-existent customer."""
    with patch("app.db.get_customer_balance") as mock_get:
        mock_get.return_value = None
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.get("/loyalty/cust-99999/balance")
            assert response.status_code == 404
            data = response.json()
            assert data["detail"]["error"] == "CUSTOMER_NOT_FOUND"

@pytest.mark.asyncio
async def test_get_balance_invalid_customer_id():
    """Test balance inquiry with invalid customer ID."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/loyalty//balance")
        assert response.status_code == 404  # Path not found
        
        # Test overly long customer ID
        long_id = "x" * 129
        response = await client.get(f"/loyalty/{long_id}/balance")
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "INVALID_CUSTOMER_ID"

@pytest.mark.asyncio
async def test_award_points_success():
    """Test awarding points on completed order."""
    with patch("app.db.check_duplicate_award") as mock_dup, \
         patch("app.db.get_customer_balance") as mock_get, \
         patch("app.db.transact_write_balance_and_transaction") as mock_write, \
         patch("app.db.get_current_timestamp") as mock_time:
        
        mock_dup.return_value = False
        mock_get.return_value = None  # New customer
        mock_time.return_value = "2025-02-14T10:30:00Z"
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/loyalty/award",
                json={
                    "customer_id": "cust-12345",
                    "order_id": "order-5000",
                    "order_total_gbp": 127.49,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["points_awarded"] == 127
            assert data["new_balance"] == 127
            assert data["created_at"] == "2025-02-14T10:30:00Z"
            assert "transaction_id" in data

@pytest.mark.asyncio
async def test_award_points_duplicate():
    """Test duplicate award prevention."""
    with patch("app.db.check_duplicate_award") as mock_dup:
        mock_dup.return_value = True  # Already awarded
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/loyalty/award",
                json={
                    "customer_id": "cust-12345",
                    "order_id": "order-5000",
                    "order_total_gbp": 100.00,
                },
            )
            assert response.status_code == 409
            data = response.json()
            assert data["detail"]["error"] == "DUPLICATE_AWARD"

@pytest.mark.asyncio
async def test_award_points_invalid_total():
    """Test award with invalid order total."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/loyalty/award",
            json={
                "customer_id": "cust-12345",
                "order_id": "order-5000",
                "order_total_gbp": -10.00,
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "INVALID_REQUEST"

@pytest.mark.asyncio
async def test_redeem_points_success():
    """Test successful points redemption."""
    with patch("app.db.get_customer_balance") as mock_get, \
         patch("app.db.transact_write_balance_and_transaction") as mock_write, \
         patch("app.db.get_current_timestamp") as mock_time:
        
        mock_get.return_value = {
            "PK": "CUSTOMER#cust-12345",
            "SK": "LOYALTY#BALANCE",
            "points_balance": 500,
            "updated_at": "2025-02-14T10:00:00Z",
        }
        mock_time.return_value = "2025-02-14T11:00:00Z"
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/loyalty/redeem",
                json={
                    "customer_id": "cust-12345",
                    "points": 200,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["discount_gbp"] == 2.00
            assert data["new_balance"] == 300
            assert "redemption_id" in data
            assert data["created_at"] == "2025-02-14T11:00:00Z"

@pytest.mark.asyncio
async def test_redeem_points_insufficient_balance():
    """Test redemption with insufficient balance."""
    with patch("app.db.get_customer_balance") as mock_get:
        mock_get.return_value = {
            "PK": "CUSTOMER#cust-12345",
            "SK": "LOYALTY#BALANCE",
            "points_balance": 150,
            "updated_at": "2025-02-14T10:00:00Z",
        }
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/loyalty/redeem",
                json={
                    "customer_id": "cust-12345",
                    "points": 200,
                },
            )
            assert response.status_code == 402
            data = response.json()
            assert data["detail"]["error"] == "INSUFFICIENT_BALANCE"

@pytest.mark.asyncio
async def test_redeem_points_minimum():
    """Test redemption minimum of 100 points."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/loyalty/redeem",
            json={
                "customer_id": "cust-12345",
                "points": 50,
            },
        )
        assert response.status_code == 400
        data = response.json()
        assert data["detail"]["error"] == "INVALID_POINTS"

@pytest.mark.asyncio
async def test_redeem_points_customer_not_found():
    """Test redemption for non-existent customer."""
    with patch("app.db.get_customer_balance") as mock_get:
        mock_get.return_value = None
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/loyalty/redeem",
                json={
                    "customer_id": "cust-99999",
                    "points": 100,
                },
            )
            assert response.status_code == 404
            data = response.json()
            assert data["detail"]["error"] == "CUSTOMER_NOT_FOUND"

@pytest.mark.asyncio
async def test_reverse_redemption_success():
    """Test successful reversal of redemption."""
    with patch("app.db.check_redemption_exists") as mock_redeem_exists, \
         patch("app.db.check_reversal_exists") as mock_reversal_exists, \
         patch("app.db.get_customer_balance") as mock_get, \
         patch("app.db.transact_write_balance_and_transaction") as mock_write, \
         patch("app.db.get_current_timestamp") as mock_time:
        
        mock_redeem_exists.return_value = True
        mock_reversal_exists.return_value = False
        mock_get.return_value = {
            "PK": "CUSTOMER#cust-12345",
            "SK": "LOYALTY#BALANCE",
            "points_balance": 300,
            "updated_at": "2025-02-14T11:00:00Z",
        }
        mock_time.return_value = "2025-02-14T11:15:00Z"
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/loyalty/reverse",
                json={
                    "customer_id": "cust-12345",
                    "redemption_id": "redemption-xyz-789",
                    "points_to_restore": 200,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["points_restored"] == 200
            assert data["new_balance"] == 500
            assert "reversal_transaction_id" in data
            assert data["created_at"] == "2025-02-14T11:15:00Z"

@pytest.mark.asyncio
async def test_reverse_redemption_not_found():
    """Test reversal of non-existent redemption."""
    with patch("app.db.check_redemption_exists") as mock_exists:
        mock_exists.return_value = False
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/loyalty/reverse",
                json={
                    "customer_id": "cust-12345",
                    "redemption_id": "redemption-xyz-999",
                    "points_to_restore": 200,
                },
            )
            assert response.status_code == 404
            data = response.json()
            assert data["detail"]["error"] == "REDEMPTION_NOT_FOUND"

@pytest.mark.asyncio
async def test_reverse_already_reversed():
    """Test reversal of already reversed redemption."""
    with patch("app.db.check_redemption_exists") as mock_redeem_exists, \
         patch("app.db.check_reversal_exists") as mock_reversal_exists:
        
        mock_redeem_exists.return_value = True
        mock_reversal_exists.return_value = True  # Already reversed
        
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/loyalty/reverse",
                json={
                    "customer_id": "cust-12345",
                    "redemption_id": "redemption-xyz-789",
                    "points_to_restore": 200,
                },
            )
            assert response.status_code == 409
            data = response.json()
            assert data["detail"]["error"] == "ALREADY_REVERSED"
