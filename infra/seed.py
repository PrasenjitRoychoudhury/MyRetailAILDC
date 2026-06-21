#!/usr/bin/env python3
"""
Seed DynamoDB with product data from FakeStoreAPI.
Usage:
  python seed.py --local     # seeds DynamoDB Local (docker-compose)
  python seed.py --aws       # seeds real AWS DynamoDB
"""
import argparse
import boto3
import requests
import uuid
from decimal import Decimal

TABLE_NAME = "retail-platform"

CATEGORIES = [
    {"slug": "electronics", "display_name": "Electronics", "description": "Gadgets and devices"},
    {"slug": "jewelery", "display_name": "Jewellery", "description": "Rings, necklaces and more"},
    {"slug": "mens-clothing", "display_name": "Men's Clothing", "description": "Shirts, trousers and jackets"},
    {"slug": "womens-clothing", "display_name": "Women's Clothing", "description": "Dresses, tops and more"},
]

def get_dynamodb(local: bool):
    if local:
        return boto3.resource(
            "dynamodb",
            endpoint_url="http://localhost:8000",
            region_name="us-east-1",
            aws_access_key_id="local",
            aws_secret_access_key="local",
        )
    return boto3.resource("dynamodb", region_name="us-east-1")

def create_table(dynamodb, local: bool):
    existing = [t.name for t in dynamodb.tables.all()]
    if TABLE_NAME in existing:
        print(f"Table {TABLE_NAME} already exists — skipping create")
        return dynamodb.Table(TABLE_NAME)

    table = dynamodb.create_table(
        TableName=TABLE_NAME,
        KeySchema=[
            {"AttributeName": "PK", "KeyType": "HASH"},
            {"AttributeName": "SK", "KeyType": "RANGE"},
        ],
        AttributeDefinitions=[
            {"AttributeName": "PK", "AttributeType": "S"},
            {"AttributeName": "SK", "AttributeType": "S"},
            {"AttributeName": "GSI1PK", "AttributeType": "S"},
            {"AttributeName": "GSI1SK", "AttributeType": "S"},
        ],
        GlobalSecondaryIndexes=[
            {
                "IndexName": "GSI1",
                "KeySchema": [
                    {"AttributeName": "GSI1PK", "KeyType": "HASH"},
                    {"AttributeName": "GSI1SK", "KeyType": "RANGE"},
                ],
                "Projection": {"ProjectionType": "ALL"},
            }
        ],
        BillingMode="PAY_PER_REQUEST",
    )
    table.wait_until_exists()
    print(f"Created table: {TABLE_NAME}")
    return table

def seed_categories(table):
    print("Seeding categories...")
    for cat in CATEGORIES:
        table.put_item(Item={
            "PK": f"CATEGORY#{cat['slug']}",
            "SK": "METADATA",
            "slug": cat["slug"],
            "display_name": cat["display_name"],
            "description": cat["description"],
            "product_count": 0,
            "entity_type": "CATEGORY",
        })
    print(f"  Seeded {len(CATEGORIES)} categories")

def seed_products(table):
    print("Fetching products from FakeStoreAPI...")
    resp = requests.get("https://fakestoreapi.com/products", timeout=15)
    products = resp.json()
    print(f"  Fetched {len(products)} products")

    cat_counts = {}
    with table.batch_writer() as batch:
        for p in products:
            product_id = str(p["id"])
            category = p["category"]
            cat_counts[category] = cat_counts.get(category, 0) + 1

            batch.put_item(Item={
                "PK": f"PRODUCT#{product_id}",
                "SK": "METADATA",
                "GSI1PK": f"CATEGORY#{category}",
                "GSI1SK": f"PRODUCT#{product_id}",
                "product_id": product_id,
                "name": p["title"],
                "description": p["description"],
                "price": Decimal(str(p["price"])),
                "category": category,
                "image_url": p["image"],
                "rating_rate": Decimal(str(p["rating"]["rate"])),
                "rating_count": p["rating"]["count"],
                "stock_qty": 100,
                "entity_type": "PRODUCT",
            })

    # update category product counts
    for slug, count in cat_counts.items():
        table.update_item(
            Key={"PK": f"CATEGORY#{slug}", "SK": "METADATA"},
            UpdateExpression="SET product_count = :c",
            ExpressionAttributeValues={":c": count},
        )

    print(f"  Seeded {len(products)} products across {len(cat_counts)} categories")

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", action="store_true", help="Seed DynamoDB Local")
    parser.add_argument("--aws", action="store_true", help="Seed AWS DynamoDB")
    args = parser.parse_args()

    if not args.local and not args.aws:
        print("Usage: python seed.py --local | --aws")
        return

    local = args.local
    print(f"Seeding {'DynamoDB Local' if local else 'AWS DynamoDB'}...")

    dynamodb = get_dynamodb(local)
    table = create_table(dynamodb, local)
    seed_categories(table)
    seed_products(table)
    print("Seed complete.")

if __name__ == "__main__":
    main()
