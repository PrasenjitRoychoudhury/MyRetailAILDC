#!/usr/bin/env python3
"""
Seed DynamoDB with test discount coupons (FR-006 / SVC-6).
Usage:
  python seed_coupons.py --local     # seeds DynamoDB Local (docker-compose)
  python seed_coupons.py --aws       # seeds real AWS DynamoDB
"""
import argparse
import time
import boto3
from decimal import Decimal

TABLE_NAME = "retail-platform"

COUPONS = [
    {"code": "SAVE10", "discount_type": "percentage", "discount_value": Decimal("10"),
     "min_order": Decimal("20"), "expires_at": "2026-12-31", "max_uses": 100},
    {"code": "FLAT5", "discount_type": "fixed", "discount_value": Decimal("5"),
     "min_order": Decimal("15"), "expires_at": "2026-12-31", "max_uses": 50},
    {"code": "WELCOME20", "discount_type": "percentage", "discount_value": Decimal("20"),
     "min_order": Decimal("0"), "expires_at": "2026-12-31", "max_uses": 200},
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


def seed_coupons(table):
    print("Seeding coupons...")
    for c in COUPONS:
        table.put_item(Item={
            "PK": f"COUPON#{c['code']}",
            "SK": "METADATA",
            "code": c["code"],
            "discount_type": c["discount_type"],
            "discount_value": c["discount_value"],
            "min_order": c["min_order"],
            "expires_at": c["expires_at"],
            "max_uses": c["max_uses"],
            "uses_count": 0,
            "active": True,
            "entity_type": "COUPON",
            "created_at": int(time.time()),
        })
        print(f"  Seeded {c['code']} ({c['discount_type']} {c['discount_value']})")
    print(f"  Seeded {len(COUPONS)} coupons")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--local", action="store_true", help="Seed DynamoDB Local")
    parser.add_argument("--aws", action="store_true", help="Seed AWS DynamoDB")
    args = parser.parse_args()

    if not args.local and not args.aws:
        print("Usage: python seed_coupons.py --local | --aws")
        return

    local = args.local
    print(f"Seeding {'DynamoDB Local' if local else 'AWS DynamoDB'}...")

    dynamodb = get_dynamodb(local)
    table = dynamodb.Table(TABLE_NAME)
    seed_coupons(table)
    print("Coupon seed complete.")


if __name__ == "__main__":
    main()
