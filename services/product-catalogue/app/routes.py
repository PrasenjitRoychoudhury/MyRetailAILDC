from fastapi import APIRouter, HTTPException, Query
from app.db import get_product_by_id, list_products
from app.models import ProductResponse, ProductDetail, ErrorResponse
from typing import Optional

router = APIRouter()

@router.get(
    "/products/{product_id}",
    response_model=ProductResponse,
    responses={
        200: {"model": ProductResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse}
    }
)
async def get_product(product_id: str):
    """
    Retrieve full product details by product ID.
    Returns product image, name, description, price, category, stock quantity,
    average rating, and rating count.
    """
    try:
        product = await get_product_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    message=f"Product {product_id} not found",
                    error_code="PRODUCT_NOT_FOUND"
                ).model_dump()
            )
        return ProductResponse(
            success=True,
            data=ProductDetail(**product)
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error",
                error_code="INTERNAL_ERROR"
            ).model_dump()
        )

@router.get(
    "/products",
    response_model=dict,
    responses={200: {"description": "List of products"}, 500: {"model": ErrorResponse}}
)
async def list_all_products(
    category: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0)
):
    """
    List all products with optional filtering by category.
    Supports pagination via limit and offset.
    """
    try:
        products, total = await list_products(category=category, limit=limit, offset=offset)
        return {
            "success": True,
            "data": products,
            "pagination": {
                "limit": limit,
                "offset": offset,
                "total": total
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                message="Internal server error",
                error_code="INTERNAL_ERROR"
            ).model_dump()
        )
