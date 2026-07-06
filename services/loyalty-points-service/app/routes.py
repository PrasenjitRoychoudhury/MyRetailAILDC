from fastapi import APIRouter, HTTPException, status
from datetime import datetime, timezone
import math
from app.models import (
    BalanceResponse,
    AwardRequest,
    AwardResponse,
    RedeemRequest,
    RedeemResponse,
    ReverseRequest,
    ReverseResponse,
    ErrorResponse,
)
from app import db

router = APIRouter(prefix="/loyalty", tags=["loyalty"])

def validate_customer_id(customer_id: str) -> None:
    """Validate customer ID format."""
    if not customer_id or len(customer_id) > 128:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_CUSTOMER_ID",
                "message": "Customer ID must be non-empty alphanumeric string, max 128 characters.",
            },
        )

def validate_order_total(order_total_gbp: float) -> None:
    """Validate order total format."""
    if order_total_gbp <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_REQUEST",
                "message": "order_total_gbp must be positive number with max 2 decimal places.",
            },
        )
    # Check 2 decimal places
    if round(order_total_gbp, 2) != order_total_gbp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_REQUEST",
                "message": "order_total_gbp must be positive number with max 2 decimal places.",
            },
        )

@router.get("/{customer_id}/balance", response_model=BalanceResponse)
async def get_balance(customer_id: str):
    """Retrieve customer's current loyalty points balance."""
    validate_customer_id(customer_id)
    
    try:
        balance_item = db.get_customer_balance(customer_id)
        if not balance_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "CUSTOMER_NOT_FOUND",
                    "message": "Customer has no loyalty account or balance record.",
                },
            )
        
        return BalanceResponse(
            customer_id=customer_id,
            points_balance=int(balance_item.get("points_balance", 0)),
            as_of=balance_item.get("updated_at", db.get_current_timestamp()),
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "DATABASE_ERROR",
                "message": "Failed to retrieve balance from DynamoDB.",
            },
        )

@router.post("/award", response_model=AwardResponse)
async def award_points(request: AwardRequest):
    """Award loyalty points on payment completion."""
    validate_customer_id(request.customer_id)
    validate_order_total(request.order_total_gbp)
    
    try:
        # Check for duplicate award
        if db.check_duplicate_award(request.customer_id, request.order_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "DUPLICATE_AWARD",
                    "message": f"Award already exists for order_id '{request.order_id}'.",
                },
            )
        
        # Calculate points (floor of order total)
        points_awarded = math.floor(request.order_total_gbp)
        
        # Get current balance or start at 0
        current_item = db.get_customer_balance(request.customer_id)
        current_balance = int(current_item.get("points_balance", 0)) if current_item else 0
        new_balance = current_balance + points_awarded
        
        # Create timestamp
        timestamp = db.get_current_timestamp()
        
        # Create balance and transaction items
        balance_item = db.create_balance_item(request.customer_id, new_balance, timestamp)
        transaction_item, txn_id = db.create_transaction_item(
            request.customer_id,
            "AWARD",
            points_awarded,
            timestamp,
            order_id=request.order_id,
            order_total_gbp=request.order_total_gbp,
        )
        
        # Atomic write
        db.transact_write_balance_and_transaction(balance_item, transaction_item, request.customer_id)
        
        return AwardResponse(
            points_awarded=points_awarded,
            new_balance=new_balance,
            transaction_id=txn_id,
            created_at=timestamp,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "DATABASE_ERROR",
                "message": "Failed to write transaction to DynamoDB.",
            },
        )

@router.post("/redeem", response_model=RedeemResponse)
async def redeem_points(request: RedeemRequest):
    """Redeem points for discount (100 points = £1)."""
    validate_customer_id(request.customer_id)
    
    if request.points < 100:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "INVALID_POINTS",
                "message": f"Minimum 100 points required for redemption; requested {request.points}.",
            },
        )
    
    try:
        # Get current balance
        balance_item = db.get_customer_balance(request.customer_id)
        if not balance_item:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "CUSTOMER_NOT_FOUND",
                    "message": "Customer has no loyalty account.",
                },
            )
        
        current_balance = int(balance_item.get("points_balance", 0))
        
        # Check sufficient balance
        if current_balance < request.points:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "error": "INSUFFICIENT_BALANCE",
                    "message": f"Customer has {current_balance} points but {request.points} requested.",
                },
            )
        
        # Calculate discount (100 points = £1.00)
        discount_gbp = round(request.points / 100, 2)
        new_balance = current_balance - request.points
        
        # Create timestamp and redemption ID
        timestamp = db.get_current_timestamp()
        import uuid
        redemption_id = f"redemption-{str(uuid.uuid4())}"
        
        # Create balance and transaction items
        new_balance_item = db.create_balance_item(request.customer_id, new_balance, timestamp)
        transaction_item, txn_id = db.create_transaction_item(
            request.customer_id,
            "REDEEM",
            -request.points,
            timestamp,
            redemption_id=redemption_id,
            discount_gbp=discount_gbp,
        )
        
        # Atomic write
        db.transact_write_balance_and_transaction(new_balance_item, transaction_item, request.customer_id)
        
        return RedeemResponse(
            discount_gbp=discount_gbp,
            new_balance=new_balance,
            redemption_id=redemption_id,
            created_at=timestamp,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "DATABASE_ERROR",
                "message": "Failed to write redemption transaction to DynamoDB.",
            },
        )

@router.post("/reverse", response_model=ReverseResponse)
async def reverse_redemption(request: ReverseRequest):
    """Reverse a previous redemption when checkout is abandoned."""
    validate_customer_id(request.customer_id)
    
    try:
        # Check if redemption exists
        if not db.check_redemption_exists(request.customer_id, request.redemption_id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": "REDEMPTION_NOT_FOUND",
                    "message": f"Redemption '{request.redemption_id}' not found for customer.",
                },
            )
        
        # Check if already reversed
        if db.check_reversal_exists(request.customer_id, request.redemption_id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": "ALREADY_REVERSED",
                    "message": "Redemption already reversed.",
                },
            )
        
        # Get current balance
        balance_item = db.get_customer_balance(request.customer_id)
        current_balance = int(balance_item.get("points_balance", 0)) if balance_item else 0
        new_balance = current_balance + request.points_to_restore
        
        # Create timestamp
        timestamp = db.get_current_timestamp()
        
        # Create balance and reversal transaction items
        new_balance_item = db.create_balance_item(request.customer_id, new_balance, timestamp)
        transaction_item, txn_id = db.create_transaction_item(
            request.customer_id,
            "REVERSAL",
            request.points_to_restore,
            timestamp,
            redemption_id=request.redemption_id,
        )
        
        # Atomic write
        db.transact_write_balance_and_transaction(new_balance_item, transaction_item, request.customer_id)
        
        return ReverseResponse(
            points_restored=request.points_to_restore,
            new_balance=new_balance,
            reversal_transaction_id=txn_id,
            created_at=timestamp,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "DATABASE_ERROR",
                "message": "Failed to write reversal transaction.",
            },
        )
