import boto3
import os
from app.models import Review, ProductRatingSummary
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
import json

TABLE_NAME = os.getenv("TABLE_NAME", "retail-platform")

class DynamoDBClient:
    def __init__(self):
        self.dynamodb = boto3.resource("dynamodb")
        self.table = self.dynamodb.Table(TABLE_NAME)
    
    async def create_review(self, review: Review) -> None:
        """
        Create a new review in DynamoDB.
        PK: REVIEW#{review_id}
        SK: PRODUCT#{product_id}
        """
        item = {
            "PK": f"REVIEW#{review.review_id}",
            "SK": f"PRODUCT#{review.product_id}",
            "product_id": review.product_id,
            "user_id": review.user_id,
            "review_id": review.review_id,
            "rating": Decimal(str(review.rating)),
            "title": review.title,
            "content": review.content,
            "created_at": review.created_at.isoformat(),
            "helpful_count": 0,
            "unhelpful_count": 0,
            "type": "REVIEW"
        }
        self.table.put_item(Item=item)
    
    async def get_review(self, review_id: str) -> Optional[Review]:
        """
        Retrieve a review by ID.
        """
        response = self.table.query(
            KeyConditionExpression="PK = :pk",
            ExpressionAttributeValues={
                ":pk": f"REVIEW#{review_id}"
            }
        )
        
        if response["Items"]:
            item = response["Items"][0]
            return self._parse_review(item)
        return None
    
    async def update_review(self, review: Review) -> None:
        """
        Update an existing review.
        """
        item = {
            "PK": f"REVIEW#{review.review_id}",
            "SK": f"PRODUCT#{review.product_id}",
            "product_id": review.product_id,
            "user_id": review.user_id,
            "review_id": review.review_id,
            "rating": Decimal(str(review.rating)),
            "title": review.title,
            "content": review.content,
            "created_at": review.created_at.isoformat(),
            "updated_at": review.updated_at.isoformat() if review.updated_at else None,
            "helpful_count": review.helpful_count,
            "unhelpful_count": review.unhelpful_count,
            "type": "REVIEW"
        }
        self.table.put_item(Item=item)
    
    async def delete_review(self, review_id: str, product_id: str) -> None:
        """
        Delete a review.
        """
        self.table.delete_item(
            Key={
                "PK": f"REVIEW#{review_id}",
                "SK": f"PRODUCT#{product_id}"
            }
        )
    
    async def get_reviews_by_product(self, product_id: str, limit: int = 10, offset: int = 0) -> List[Review]:
        """
        Get all reviews for a product.
        Uses GSI: SK = PRODUCT#{product_id}
        """
        response = self.table.query(
            IndexName="SK-index",
            KeyConditionExpression="SK = :sk",
            ExpressionAttributeValues={
                ":sk": f"PRODUCT#{product_id}"
            },
            Limit=limit + offset
        )
        
        items = response.get("Items", [])
        reviews = [self._parse_review(item) for item in items[offset:offset+limit]]
        return reviews
    
    async def get_product_rating_summary(self, product_id: str) -> ProductRatingSummary:
        """
        Get rating summary for a product.
        PK: PRODUCT#{product_id}
        SK: METADATA
        """
        response = self.table.get_item(
            Key={
                "PK": f"PRODUCT#{product_id}",
                "SK": "METADATA"
            }
        )
        
        if "Item" in response:
            item = response["Item"]
            rating_dist = json.loads(item.get("rating_distribution", "{}")) if isinstance(item.get("rating_distribution"), str) else item.get("rating_distribution", {})
            return ProductRatingSummary(
                product_id=product_id,
                average_rating=float(item.get("average_rating", 0)),
                rating_count=int(item.get("rating_count", 0)),
                rating_distribution={int(k): int(v) for k, v in rating_dist.items()}
            )
        
        return ProductRatingSummary(
            product_id=product_id,
            average_rating=0.0,
            rating_count=0,
            rating_distribution={}
        )
    
    async def update_product_rating(self, product_id: str, new_rating: int) -> None:
        """
        Update product rating summary after a new review.
        """
        summary = await self.get_product_rating_summary(product_id)
        
        total_rating = (summary.average_rating * summary.rating_count) + new_rating
        new_count = summary.rating_count + 1
        new_average = total_rating / new_count
        
        rating_dist = summary.rating_distribution.copy()
        rating_dist[new_rating] = rating_dist.get(new_rating, 0) + 1
        
        item = {
            "PK": f"PRODUCT#{product_id}",
            "SK": "METADATA",
            "product_id": product_id,
            "average_rating": Decimal(str(round(new_average, 2))),
            "rating_count": new_count,
            "rating_distribution": json.dumps(rating_dist),
            "type": "PRODUCT_METADATA"
        }
        self.table.put_item(Item=item)
    
    async def update_review_helpful(self, review_id: str, is_helpful: bool) -> None:
        """
        Update helpful/unhelpful count for a review.
        """
        review = await self.get_review(review_id)
        if review:
            if is_helpful:
                review.helpful_count += 1
            else:
                review.unhelpful_count += 1
            await self.update_review(review)
    
    def _parse_review(self, item: dict) -> Review:
        """
        Parse DynamoDB item to Review model.
        """
        return Review(
            review_id=item.get("review_id"),
            product_id=item.get("product_id"),
            user_id=item.get("user_id"),
            rating=int(item.get("rating", 0)),
            title=item.get("title"),
            content=item.get("content"),
            created_at=datetime.fromisoformat(item.get("created_at")),
            updated_at=datetime.fromisoformat(item.get("updated_at")) if item.get("updated_at") else None,
            helpful_count=int(item.get("helpful_count", 0)),
            unhelpful_count=int(item.get("unhelpful_count", 0))
        )
