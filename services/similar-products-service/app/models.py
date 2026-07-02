from pydantic import BaseModel, Field
from typing import Optional
from decimal import Decimal

class ProductRating(BaseModel):
    rate: float = Field(default=0.0, alias="rating_rate")
    count: int = Field(default=0, alias="rating_count")

    class Config:
        populate_by_name = True

class ProductDetail(BaseModel):
    product_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    price: float
    stock_qty: Optional[int] = None
    image_url: Optional[str] = None
    rating: Optional[ProductRating] = None

    class Config:
        from_attributes = True

class SimilarProductsResponse(BaseModel):
    product_id: str
    similar_products: list[ProductDetail]
    count: int

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
