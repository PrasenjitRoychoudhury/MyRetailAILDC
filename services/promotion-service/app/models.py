from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PromotionType(str, Enum):
    PERCENT = "PERCENT"
    FIXED = "FIXED"
    BOGO = "BOGO"

class PromotionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    promo_code: str = Field(..., min_length=1, max_length=50)
    promotion_type: PromotionType
    value: float = Field(..., gt=0)
    start_date: datetime
    end_date: datetime
    usage_limit: Optional[int] = Field(None, ge=0)
    min_cart_value: Optional[float] = Field(None, ge=0)
    applicable_categories: Optional[List[str]] = Field(None)

class PromotionResponse(BaseModel):
    promo_id: str
    name: str
    promo_code: str
    promotion_type: PromotionType
    value: float
    start_date: str
    end_date: str
    usage_limit: Optional[int]
    usage_count: int
    min_cart_value: Optional[float]
    applicable_categories: Optional[List[str]]

class ValidatePromotionRequest(BaseModel):
    promo_code: str
    cart_total: float = Field(..., ge=0)
    user_id: str

class ValidatePromotionResponse(BaseModel):
    valid: bool
    discount_amount: float
    message: str

class ApplyPromotionRequest(BaseModel):
    promo_code: str
    order_id: str
    user_id: str

class ApplyPromotionResponse(BaseModel):
    applied: bool
    discount_amount: float
    message: str

class PromoUsage(BaseModel):
    user_id: str
    promo_id: str
    used_at: str
    order_id: str
