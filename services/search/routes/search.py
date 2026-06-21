import os, time, boto3
from fastapi import APIRouter, Query
from boto3.dynamodb.conditions import Attr
from typing import Optional

router = APIRouter(tags=["search"])
TABLE = os.environ.get("DYNAMODB_TABLE", "retail-platform")
ENDPOINT = os.environ.get("DYNAMODB_ENDPOINT")

def table():
    kw = {"region_name": os.environ.get("AWS_DEFAULT_REGION","us-east-1")}
    if ENDPOINT: kw["endpoint_url"] = ENDPOINT
    return boto3.resource("dynamodb", **kw).Table(TABLE)

@router.get("/search")
def search(q: str = Query(..., min_length=1), category: Optional[str] = Query(None),
           min_price: Optional[float] = None, max_price: Optional[float] = None, limit: int = 20):
    t0 = time.time()
    t = table()
    q_lower = q.lower()
    filter_expr = (Attr("entity_type").eq("PRODUCT") &
                   (Attr("name").contains(q_lower) | Attr("description").contains(q_lower)))
    if category:
        filter_expr = filter_expr & Attr("category").eq(category)
    resp = t.scan(FilterExpression=filter_expr)
    results = resp.get("Items", [])
    if min_price is not None:
        results = [r for r in results if float(r.get("price", 0)) >= min_price]
    if max_price is not None:
        results = [r for r in results if float(r.get("price", 0)) <= max_price]
    results = results[:limit]
    return {"results": [{"product_id": r["product_id"], "name": r["name"],
        "price": float(r["price"]), "category": r["category"],
        "image_url": r.get("image_url",""), "rating_rate": float(r.get("rating_rate",0))}
        for r in results], "total": len(results), "query_time_ms": round((time.time()-t0)*1000)}

@router.get("/search/suggest")
def suggest(q: str = Query(..., min_length=1), limit: int = 5):
    t = table()
    q_lower = q.lower()
    resp = t.scan(FilterExpression=Attr("entity_type").eq("PRODUCT") & Attr("name").contains(q_lower))
    items = resp.get("Items", [])[:limit]
    return {"suggestions": [i["name"] for i in items]}
