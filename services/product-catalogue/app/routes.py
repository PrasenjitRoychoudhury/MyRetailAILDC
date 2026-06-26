from fastapi import APIRouter, HTTPException, Query
from app.models import ProductResponse, ProductDetail, RatingInfo
from app.db import get_product_by_id

router = APIRouter(prefix="/v1", tags=["products"])

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product_detail(product_id: str):
    """
    Retrieve full product details by product ID.
    Returns product image, name, description, price, category, stock quantity, and rating info.
    """
    try:
        product_data = await get_product_by_id(product_id)
        
        if not product_data:
            raise HTTPException(
                status_code=404,
                detail=f"Product with ID {product_id} not found"
            )
        
        rating = RatingInfo(
            average_rating=product_data.get("average_rating", 0.0),
            rating_count=product_data.get("rating_count", 0)
        )
        
        product = ProductDetail(
            id=product_data["product_id"],
            name=product_data["name"],
            description=product_data["description"],
            price=product_data["price"],
            category=product_data["category"],
            stock_quantity=product_data["stock_quantity"],
            image_url=product_data["image_url"],
            rating=rating
        )
        
        return ProductResponse(success=True, data=product)
    
    except HTTPException:
        raise
    except Exception as e:
        return ProductResponse(
            success=False,
            error=f"Internal server error: {str(e)}"
        )

@router.get("/products", response_model=dict)
async def list_products(category: str = Query(None), limit: int = Query(20, ge=1, le=100)):
    """
    List products with optional category filtering.
    """
    try:
        products = await get_product_by_id(None, category=category, limit=limit)
        return {"success": True, "data": products, "count": len(products)}
    except Exception as e:
        return {"success": False, "error": str(e)}
