# CLAUDE.md — User & Auth Service (SVC-4)
## Owned DynamoDB Key Prefixes
- PK: `USER#<user_id>` SK: `METADATA`
- GSI1PK: `EMAIL#<email>` GSI1SK: `USER#<user_id>`
## FORBIDDEN: PRODUCT# CATEGORY# CART# ORDER# SEARCH#
## Phase 0: Guest checkout only — registration/login in Phase 1
## JWT_SECRET must be in Secrets Manager in prod, env var locally
## Confluence: FR-004
