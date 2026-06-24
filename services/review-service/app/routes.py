from fastapi import APIRouter, HTTPException, Query
from app.models import (
    ReviewCreate,
    Review,
    ProductRatingSummary,
    ProductReviewsResponse,
    ReviewHelpfulRequest,
    ErrorResponse
)
from app.db import DynamoDBClient
import uuid
from datetime import datetime

router = APIRouter(tags=["reviews"])
db_client = DynamoDBClient()

@router.post("/reviews", response_model=Review, status_code=201)
async def create_review(review_data: ReviewCreate):
    """
    Create a new product review.
    """
    try:
        review_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        review = Review(
            review_id=review_id,
            product_id=review_data.product_id,
            user_id=review_data.user_id,
            rating=review_data.rating,
            title=review_data.title,
            content=review_data.content,
            created_at=now,
            helpful_count=0,
            unhelpful_count=0
        )
        
        await db_client.create_review(review)
        await db_client.update_product_rating(review_data.product_id, review_data.rating)
        
        return review
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/products/{product_id}/reviews", response_model=ProductReviewsResponse)
async def get_product_reviews(
    product_id: str,
    limit: int = Query(10, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    Get all reviews and rating summary for a product.
    """
    try:
        summary = await db_client.get_product_rating_summary(product_id)
        reviews = await db_client.get_reviews_by_product(product_id, limit, offset)
        
        return ProductReviewsResponse(
            product_id=product_id,
            summary=summary,
            reviews=reviews,
            total_reviews=len(reviews)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/products/{product_id}/rating", response_model=ProductRatingSummary)
async def get_product_rating_summary(product_id: str):
    """
    Get rating summary for a product.
    """
    try:
        summary = await db_client.get_product_rating_summary(product_id)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/reviews/{review_id}", response_model=Review)
async def get_review(review_id: str):
    """
    Get a specific review by ID.
    """
    try:
        review = await db_client.get_review(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        return review
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/reviews/{review_id}", response_model=Review)
async def update_review(review_id: str, review_data: ReviewCreate):
    """
    Update an existing review.
    """
    try:
        existing = await db_client.get_review(review_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Review not found")
        
        updated_review = Review(
            review_id=review_id,
            product_id=review_data.product_id,
            user_id=review_data.user_id,
            rating=review_data.rating,
            title=review_data.title,
            content=review_data.content,
            created_at=existing.created_at,
            updated_at=datetime.utcnow(),
            helpful_count=existing.helpful_count,
            unhelpful_count=existing.unhelpful_count
        )
        
        await db_client.update_review(updated_review)
        return updated_review
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/reviews/{review_id}", status_code=204)
async def delete_review(review_id: str):
    """
    Delete a review.
    """
    try:
        existing = await db_client.get_review(review_id)
        if not existing:
            raise HTTPException(status_code=404, detail="Review not found")
        
        await db_client.delete_review(review_id, existing.product_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/reviews/{review_id}/helpful", status_code=200)
async def mark_review_helpful(review_id: str, request: ReviewHelpfulRequest):
    """
    Mark a review as helpful or unhelpful.
    """
    try:
        review = await db_client.get_review(review_id)
        if not review:
            raise HTTPException(status_code=404, detail="Review not found")
        
        await db_client.update_review_helpful(review_id, request.helpful)
        return {"status": "success", "review_id": review_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
