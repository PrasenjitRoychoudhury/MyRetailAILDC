# CLAUDE.md — Wishlist Service (SVC-7)

## Owned DynamoDB Key Prefixes
- PK: `SHARE#<shareToken>` SK: `META` — share-token lookup record (exclusively owned)

## Shared DynamoDB Key Prefixes (USER# is co-owned with user-auth SVC-4)
- PK: `USER#<userId>` SK: `WISHLIST#default` — wishlist metadata (name, shareToken, createdAt, updatedAt)
- PK: `USER#<userId>` SK: `WISHLIST_ITEM#<productId>` — wishlist item snapshot (productId, name, price, imageUrl, addedAt)

## FORBIDDEN Key Prefixes
- `PRODUCT#*` `CATEGORY#*` `ORDER#*` `CART#*` `SEARCH#*` `COUPON#*`
- Under `USER#`: any SK that does not start with `WISHLIST` is forbidden

## Key Rules
- Wishlist items have NO TTL — they are permanent until explicitly removed
- Share tokens are stable: once generated, the same token is returned on repeated POST /wishlist/share
- The `SHARE#<token>` record enables O(1) lookup by share token without a GSI scan
- Prices are snapshotted at add-to-wishlist time — never re-fetched from product catalogue
- move-to-cart is best-effort: call cart service first, then remove from wishlist on success only
- Auth: Bearer JWT decoded with WISHLIST_JWT_SECRET; extract `sub` (or fallback `user_id`) claim

## Environment Variables
- `WISHLIST_JWT_SECRET` — JWT signing secret (same value as user-auth service)
- `DYNAMODB_TABLE_NAME` — DynamoDB table name (default: retail-platform)
- `CART_SERVICE_URL` — internal URL of the cart service
- `AWS_REGION` — AWS region (default: us-east-1)
- `DYNAMODB_ENDPOINT` — optional, for local DynamoDB

## Confluence: FR-012
