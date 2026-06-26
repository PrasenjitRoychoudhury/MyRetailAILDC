from pydantic import BaseModel, Field
from typing import Optional

class RatingInfo(BaseModel):
    average_rating: float = Field(..., ge=0.0, le=5.0)
    rating_count: int = Field(..., ge=0)

class ProductDetail(BaseModel):
    product_id: str = Field(..., alias="id")
    name: str
    description: str
    price: float = Field(..., gt=0)
    category: str
    stock_quantity: int = Field(..., ge=0)
    image_url: str
    rating: RatingInfo

    class Config:
        populate_by_name = True

class ProductResponse(BaseModel):
    success: bool
    data: Optional[ProductDetail] = None
    error: Optional[str] = None

class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(..., ge=1, le=10)
