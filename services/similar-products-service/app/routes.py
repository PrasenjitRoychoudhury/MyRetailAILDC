from fastapi import APIRouter, HTTPException, Query
from app.db import get_product_by_id, get_products_by_category
from app.models import SimilarProductsResponse, ProductDetail, ProductRating, ErrorResponse
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1", tags=["products"])

def _format_product(item: dict) -> ProductDetail:
    """Convert DynamoDB item to ProductDetail model."""
    return ProductDetail(
        product_id=item.get("product_id", ""),
        name=item.get("name", ""),
        description=item.get("description", None),
        category=item.get("category", None),
        price=float(item.get("price", 0)),
        stock_qty=item.get("stock_qty", None),
        image_url=item.get("image_url", None),
        rating=ProductRating(
            rating_rate=float(item.get("rating_rate", 0)),
            rating_count=int(item.get("rating_count", 0))
        ) if item.get("rating_rate") or item.get("rating_count") else None
    )

@router.get(
    "/products/{product_id}/similar",
    response_model=SimilarProductsResponse,
    responses={
        404: {"model": ErrorResponse, "description": "Product not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_similar_products(
    product_id: str,
    limit: int = Query(10, ge=1, le=50, description="Max number of similar products")
) -> SimilarProductsResponse:
    """
    Get products similar to the specified product by category.
    
    Returns the target product's category and up to `limit` products from that category,
    excluding the product itself.
    """
    try:
        # Get the target product
        product = get_product_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product with id '{product_id}' not found"
            )
        
        category = product.get("category")
        if not category:
            # No category, return empty similar products
            return SimilarProductsResponse(
                product_id=product_id,
                similar_products=[],
                count=0
            )
        
        # Get all products in the same category
        category_products = get_products_by_category(category)
        
        # Filter out the current product and limit results
        similar = [
            _format_product(item)
            for item in category_products
            if item.get("product_id") != product_id
        ][:limit]
        
        return SimilarProductsResponse(
            product_id=product_id,
            similar_products=similar,
            count=len(similar)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching similar products for {product_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch similar products"
        )

@router.get(
    "/products/{product_id}",
    response_model=ProductDetail,
    responses={
        404: {"model": ErrorResponse, "description": "Product not found"},
        500: {"model": ErrorResponse, "description": "Internal server error"}
    }
)
async def get_product(product_id: str) -> ProductDetail:
    """
    Get full product details by product_id.
    
    Returns product image, name, description, price, category, stock quantity,
    average rating and rating count.
    """
    try:
        product = get_product_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=404,
                detail=f"Product with id '{product_id}' not found"
            )
        
        return _format_product(product)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching product {product_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch product details"
        )
