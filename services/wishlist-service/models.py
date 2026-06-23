from pydantic import BaseModel
from typing import List, Optional


class AddItemReq(BaseModel):
    productId: str
    name: str
    price: float
    imageUrl: str


class WishlistItem(BaseModel):
    productId: str
    name: str
    price: float
    imageUrl: str
    addedAt: str


class WishlistInfo(BaseModel):
    name: str
    shareToken: Optional[str] = None


class GetWishlistResponse(BaseModel):
    wishlist: WishlistInfo
    items: List[WishlistItem]


class ShareResponse(BaseModel):
    shareToken: str
    shareUrl: str


class SharedWishlistResponse(BaseModel):
    wishlistName: str
    ownerUserId: str
    items: List[WishlistItem]
