from fastapi import APIRouter
from app.models import SimilarProductsResponse, SimilarProduct
from app.db import get_product, scan_products_by_category
from decimal import Decimal

router = APIRouter(prefix="/v1", tags=["similar-products"])

def _f(val):
    if isinstance(val, Decimal): return float(val)
    try: return float(val)
    except: return 0.0

@router.get("/similar/{product_id}")
async def get_similar_products(product_id: str) -> SimilarProductsResponse:
    product = get_product(product_id)
    if not product:
        return SimilarProductsResponse(product_id=product_id, similar_products=[], count=0)

    category = product.get("category")
    if not category:
        return SimilarProductsResponse(product_id=product_id, similar_products=[], count=0)

    products_in_category = scan_products_by_category(category)

    similar = []
    for p in products_in_category:
        pid = p.get("product_id", p.get("id", ""))
        if pid == product_id:
            continue
        similar.append(SimilarProduct(
            product_id=pid,
            name=p.get("name", ""),
            price=_f(p.get("price", 0)),
            image_url=p.get("image_url", ""),
            rating=_f(p.get("rating_rate", p.get("rating", {}).get("average_rating", 0) if isinstance(p.get("rating"), dict) else 0))
        ))

    similar.sort(key=lambda x: x.rating, reverse=True)
    similar = similar[:4]
    return SimilarProductsResponse(product_id=product_id, similar_products=similar, count=len(similar))
