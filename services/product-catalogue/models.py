from pydantic import BaseModel
from typing import Optional, List

class Product(BaseModel):
    product_id: str
    name: str
    description: str
    price: float
    category: str
    image_url: str
    rating_rate: float
    rating_count: int
    stock_qty: int

class Category(BaseModel):
    slug: str
    display_name: str
    description: str
    product_count: int

class ProductListResponse(BaseModel):
    products: List[Product]
    total: int
    next_cursor: Optional[str] = None

class CategoryListResponse(BaseModel):
    categories: List[Category]

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
