from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class CouponCreate(BaseModel):
    coupon_code: str = Field(..., min_length=1, max_length=50)
    discount_type: str = Field(..., pattern="^(percentage|fixed)$")
    discount_value: float = Field(..., gt=0)
    min_order_value: Optional[float] = Field(default=0.0, ge=0)
    max_uses: Optional[int] = Field(default=None, gt=0)
    expiry_date: Optional[str] = Field(default=None, description="ISO 8601 date string")
    applicable_categories: Optional[list[str]] = Field(default_factory=list)
    applicable_product_ids: Optional[list[str]] = Field(default_factory=list)


class CouponUpdate(BaseModel):
    discount_type: Optional[str] = Field(default=None, pattern="^(percentage|fixed)$")
    discount_value: Optional[float] = Field(default=None, gt=0)
    min_order_value: Optional[float] = Field(default=None, ge=0)
    max_uses: Optional[int] = Field(default=None, gt=0)
    expiry_date: Optional[str] = None
    applicable_categories: Optional[list[str]] = None
    applicable_product_ids: Optional[list[str]] = None
    active: Optional[bool] = None


class CouponResponse(BaseModel):
    coupon_code: str
    discount_type: str
    discount_value: float
    min_order_value: float
    max_uses: Optional[int]
    times_used: int
    expiry_date: Optional[str]
    applicable_categories: list[str]
    applicable_product_ids: list[str]
    active: bool
    created_at: str
    updated_at: str


class ValidateCouponRequest(BaseModel):
    coupon_code: str
    order_value: float = Field(..., gt=0)
    product_ids: Optional[list[str]] = Field(default_factory=list)
    categories: Optional[list[str]] = Field(default_factory=list)


class ValidateCouponResponse(BaseModel):
    valid: bool
    discount_amount: float
    final_order_value: float
    message: str
    coupon_code: str
