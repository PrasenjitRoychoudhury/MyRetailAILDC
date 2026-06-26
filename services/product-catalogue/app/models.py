from pydantic import BaseModel, Field
from typing import Optional

class ProductRating(BaseModel):
    average_rating: float = Field(..., ge=0, le=5)
    rating_count: int = Field(..., ge=0)

class ProductDetail(BaseModel):
    product_id: str = Field(..., alias="id")
    name: str
    description: str
    price: float = Field(..., gt=0)
    category: str
    stock_quantity: int = Field(..., ge=0)
    image_url: str
    rating: ProductRating
    
    class Config:
        populate_by_name = True

class CartItem(BaseModel):
    product_id: str
    quantity: int = Field(..., ge=1, le=10)

class ProductResponse(BaseModel):
    success: bool
    data: Optional[ProductDetail] = None
    message: Optional[str] = None

class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    error_code: str
