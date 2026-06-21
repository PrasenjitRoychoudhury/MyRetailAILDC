# CLAUDE.md — Order Service (SVC-3)
## Owned DynamoDB Key Prefixes
- PK: `ORDER#<order_id>` SK: `METADATA`
- PK: `ORDER#<order_id>` SK: `ITEM#<product_id>`
- GSI1PK: `USER#<user_id>` GSI1SK: `ORDER#<created_at>`
## FORBIDDEN: PRODUCT# CATEGORY# CART# USER# SEARCH#
## Status machine: PENDING → CONFIRMED → SHIPPED → DELIVERED → CANCELLED
## Confluence: FR-005
