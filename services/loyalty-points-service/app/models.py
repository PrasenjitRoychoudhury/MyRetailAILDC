from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

class BalanceResponse(BaseModel):
    customer_id: str = Field(..., alias="customer_id")
    points_balance: int
    as_of: str

class AwardRequest(BaseModel):
    customer_id: str = Field(..., max_length=128)
    order_id: str = Field(..., max_length=128)
    order_total_gbp: float = Field(..., gt=0)

class AwardResponse(BaseModel):
    points_awarded: int
    new_balance: int
    transaction_id: str
    created_at: str

class RedeemRequest(BaseModel):
    customer_id: str = Field(..., max_length=128)
    points: int = Field(..., ge=100)

class RedeemResponse(BaseModel):
    discount_gbp: float
    new_balance: int
    redemption_id: str
    created_at: str

class ReverseRequest(BaseModel):
    customer_id: str = Field(..., max_length=128)
    redemption_id: str
    points_to_restore: int = Field(..., ge=1)

class ReverseResponse(BaseModel):
    points_restored: int
    new_balance: int
    reversal_transaction_id: str
    created_at: str

class ErrorResponse(BaseModel):
    error: str
    message: str

class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: str
