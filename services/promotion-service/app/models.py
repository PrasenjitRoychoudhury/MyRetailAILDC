from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

class PromotionType(str, Enum):
    PERCENT = "PERCENT"
    FIXED = "FIXED"
    BOGO = "BOGO"

class PromotionCreate(BaseModel):
    promoCode: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=255)
    promoType: PromotionType
    value: float = Field(..., gt=0)
    startDate: datetime
    endDate: datetime
    usageLimit: int = Field(..., ge=0)
    minCartValue: float = Field(default=0, ge=0)
    applicableCategories: Optional[List[str]] = Field(default_factory=list)

class PromotionResponse(BaseModel):
    promoId: str
    promoCode: str
    name: str
    promoType: PromotionType
    value: float
    startDate: str
    endDate: str
    usageLimit: int
    usageCount: int
    minCartValue: float
    applicableCategories: List[str]
    createdAt: str

class ValidatePromoRequest(BaseModel):
    promoCode: str = Field(..., min_length=1)
    cartTotal: float = Field(..., ge=0)
    userId: str = Field(..., min_length=1)

class ValidatePromoResponse(BaseModel):
    valid: bool
    discountAmount: float
    message: str
    promoId: Optional[str] = None

class ApplyPromoRequest(BaseModel):
    promoCode: str = Field(..., min_length=1)
    orderId: str = Field(..., min_length=1)
    userId: str = Field(..., min_length=1)

class ApplyPromoResponse(BaseModel):
    applied: bool
    discountAmount: float
    message: str
    promoId: Optional[str] = None

class PromoUsageRecord(BaseModel):
    userId: str
    promoId: str
    orderId: str
    usedAt: str
