from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PromotionType(str, Enum):
    PERCENT = "PERCENT"
    FIXED = "FIXED"
    BOGO = "BOGO"

class PromotionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: PromotionType
    value: float = Field(..., gt=0)
    start_date: datetime
    end_date: datetime
    usage_limit: int = Field(..., ge=1)
    min_cart_value: float = Field(default=0, ge=0)
    applicable_categories: List[str] = Field(default_factory=list)

class PromotionCreate(PromotionBase):
    pass

class PromotionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    value: Optional[float] = Field(None, gt=0)
    end_date: Optional[datetime] = None
    usage_limit: Optional[int] = Field(None, ge=1)

class Promotion(PromotionBase):
    promo_id: str
    usage_count: int = 0
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class ValidatePromoRequest(BaseModel):
    promo_code: str = Field(..., min_length=1)
    cart_total: float = Field(..., gt=0)
    user_id: str = Field(..., min_length=1)

class ValidatePromoResponse(BaseModel):
    valid: bool
    discount_amount: float = 0
    message: str

class ApplyPromoRequest(BaseModel):
    promo_code: str = Field(..., min_length=1)
    order_id: str = Field(..., min_length=1)
    user_id: str = Field(..., min_length=1)

class ApplyPromoResponse(BaseModel):
    applied: bool
    discount_amount: float = 0

class UpdatePromotionResponse(BaseModel):
    updated: bool
    promotion: Optional[Promotion] = None

class DeletePromotionResponse(BaseModel):
    deleted: bool
    promo_id: str

class PromoUsage(BaseModel):
    used_at: datetime
    order_id: str
