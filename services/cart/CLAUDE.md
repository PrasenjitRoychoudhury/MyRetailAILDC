# CLAUDE.md — Shopping Cart Service (SVC-2)
## Owned DynamoDB Key Prefixes
- PK: `CART#<session_id>` SK: `ITEM#<product_id>` (cart items)
- PK: `CART#<session_id>` SK: `METADATA` (cart metadata, TTL 7 days)
## FORBIDDEN Key Prefixes
- `PRODUCT#*` `CATEGORY#*` `ORDER#*` `USER#*` `SEARCH#*`
## Key Rules
- Cart items have TTL of 604800 seconds (7 days) — always set expires_at
- Validate product_id by calling SVC-1 GET /v1/products/{id} before adding to cart
- Snapshot price at add-to-cart time — never re-fetch price
- On checkout: publish cart.checked_out to EventBridge retail-events bus
## Confluence: FR-003
