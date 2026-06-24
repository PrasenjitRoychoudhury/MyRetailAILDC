from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class ReviewCreate(BaseModel):
    product_id: str = Field(..., min_length=1, description="Product ID")
    user_id: str = Field(..., min_length=1, description="User ID")
    rating: int = Field(..., ge=1, le=5, description="Rating from 1 to 5")
    title: str = Field(..., min_length=1, max_length=200, description="Review title")
    content: str = Field(..., min_length=1, max_length=2000, description="Review content")

class Review(ReviewCreate):
    review_id: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    helpful_count: int = 0
    unhelpful_count: int = 0

class ProductRatingSummary(BaseModel):
    product_id: str
    average_rating: float = Field(..., ge=0, le=5, description="Average rating")
    rating_count: int = Field(..., ge=0, description="Total number of ratings")
    rating_distribution: dict[int, int] = Field(default_factory=dict, description="Distribution of ratings 1-5")

class ProductReviewsResponse(BaseModel):
    product_id: str
    summary: ProductRatingSummary
    reviews: list[Review] = []
    total_reviews: int = 0

class ReviewHelpfulRequest(BaseModel):
    helpful: bool = Field(..., description="True for helpful, False for unhelpful")

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
    status_code: int
