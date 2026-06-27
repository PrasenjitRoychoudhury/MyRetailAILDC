from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from app.models import SimilarProductsResponse, SimilarProductItem
from app.db import get_product_by_id, get_similar_products

router = APIRouter(prefix="/v1", tags=["similar-products"])


@router.get("/similar/{product_id}")
async def similar_products(product_id: str) -> JSONResponse:
    """
    Retrieve up to 4 similar products from the same category.
    Returns HTTP 200 for all scenarios (product found, not found, or empty category).
    """
    product = get_product_by_id(product_id)

    if not product:
        return JSONResponse(
            status_code=200,
            content={
                "product_id": product_id,
                "similar_products": [],
                "count": 0
            }
        )

    category = product.get("category")

    if not category:
        return JSONResponse(
            status_code=200,
            content={
                "product_id": product_id,
                "similar_products": [],
                "count": 0
            }
        )

    similar_items = get_similar_products(category, exclude_product_id=product_id)

    similar_products_list = []
    for item in similar_items[:4]:
        rating_map = item.get("rating", {})
        average_rating = float(rating_map.get("average_rating", 0))

        similar_product = SimilarProductItem(
            product_id=item.get("id", ""),
            name=item.get("name", ""),
            price=float(item.get("price", 0)),
            image_url=item.get("image_url", ""),
            rating=average_rating
        )
        similar_products_list.append(similar_product)

    return JSONResponse(
        status_code=200,
        content={
            "product_id": product_id,
            "similar_products": [p.model_dump(by_alias=True) for p in similar_products_list],
            "count": len(similar_products_list)
        }
    )
