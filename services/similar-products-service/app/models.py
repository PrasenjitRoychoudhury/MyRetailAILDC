from pydantic import BaseModel, Field
from typing import List

class SimilarProduct(BaseModel):
    product_id: str
    name: str
    price: float
    image_url: str
    rating_rate: float

class SimilarProductsResponse(BaseModel):
    product_id: str
    similar_products: List[SimilarProduct] = Field(default_factory=list)
    count: int
