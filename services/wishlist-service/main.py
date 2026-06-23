import os
import requests
from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware

from models import (
    AddItemReq, GetWishlistResponse, ShareResponse,
    SharedWishlistResponse, WishlistInfo, WishlistItem,
)
from auth import get_current_user
import dynamo

app = FastAPI(title="Wishlist Service", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

CART_URL = os.environ.get("CART_SERVICE_URL", "http://localhost:8002")


@app.get("/v1/health")
def health():
    return {"status": "ok", "service": "wishlist", "version": "1.0.0"}


@app.post("/v1/wishlist/items")
def add_item(req: AddItemReq, user_id: str = Depends(get_current_user)):
    dynamo.add_item(user_id, req.productId, req.name, req.price, req.imageUrl)
    return {"message": "Added to wishlist"}


@app.delete("/v1/wishlist/items/{product_id}")
def remove_item(product_id: str, user_id: str = Depends(get_current_user)):
    dynamo.remove_item(user_id, product_id)
    return {"message": "Removed from wishlist"}


@app.get("/v1/wishlist", response_model=GetWishlistResponse)
def get_wishlist(user_id: str = Depends(get_current_user)):
    meta, items = dynamo.get_wishlist(user_id)
    return GetWishlistResponse(
        wishlist=WishlistInfo(
            name=(meta or {}).get("name", "My Wishlist"),
            shareToken=(meta or {}).get("shareToken"),
        ),
        items=[
            WishlistItem(
                productId=i["productId"],
                name=i["name"],
                price=float(i["price"]),
                imageUrl=i["imageUrl"],
                addedAt=i["addedAt"],
            )
            for i in items
        ],
    )


@app.post("/v1/wishlist/share", response_model=ShareResponse)
def generate_share(user_id: str = Depends(get_current_user)):
    token = dynamo.get_or_create_share_token(user_id)
    return ShareResponse(shareToken=token, shareUrl=f"/api/wishlist/shared/{token}")


@app.get("/v1/wishlist/shared/{token}", response_model=SharedWishlistResponse)
def get_shared(token: str):
    user_id, wishlist_name, items = dynamo.get_shared_wishlist(token)
    if user_id is None:
        raise HTTPException(status_code=404, detail="Shared wishlist not found")
    return SharedWishlistResponse(
        wishlistName=wishlist_name,
        ownerUserId=user_id,
        items=[
            WishlistItem(
                productId=i["productId"],
                name=i["name"],
                price=float(i["price"]),
                imageUrl=i["imageUrl"],
                addedAt=i["addedAt"],
            )
            for i in items
        ],
    )


@app.post("/v1/wishlist/items/{product_id}/move-to-cart")
def move_to_cart(
    product_id: str,
    user_id: str = Depends(get_current_user),
    authorization: str = Header(None),
):
    _, wish_items = dynamo.get_wishlist(user_id)
    item = next((i for i in wish_items if i["productId"] == product_id), None)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found in wishlist")
    try:
        # Cart is session-based; use user_id as the cart session for authenticated users
        r = requests.post(
            f"{CART_URL}/v1/cart/{user_id}/items",
            json={"product_id": product_id, "qty": 1},
            headers={"Authorization": authorization} if authorization else {},
            timeout=5,
        )
        if r.status_code not in (200, 201):
            raise HTTPException(status_code=502, detail="Cart service returned an error")
    except requests.exceptions.RequestException:
        raise HTTPException(status_code=503, detail="Cart service unavailable")
    dynamo.remove_item(user_id, product_id)
    return {"message": "Moved to cart"}
