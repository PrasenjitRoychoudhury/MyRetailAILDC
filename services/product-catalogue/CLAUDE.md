# CLAUDE.md — Product Catalogue Service (SVC-1)

## Service Purpose
Owns all product and category master data. The single authoritative source for product information.
Every other service that needs product data calls this service — never reads DynamoDB product items directly.

## Owned DynamoDB Key Prefixes
- PK: `PRODUCT#<product_id>` SK: `METADATA`
- PK: `CATEGORY#<slug>` SK: `METADATA`
- GSI1PK: `CATEGORY#<slug>` GSI1SK: `PRODUCT#<product_id>`

## FORBIDDEN Key Prefixes (never read or write)
- `CART#*` — owned by Cart Service (SVC-2)
- `ORDER#*` — owned by Order Service (SVC-3)
- `USER#*` — owned by User & Auth Service (SVC-4)
- `SEARCH#*` — owned by Search Service (SVC-5)

## API Contract
See /docs/openapi.yaml. Never add endpoints without updating openapi.yaml first.

## Coding Conventions
- Python 3.12, FastAPI, pydantic v2
- All responses use the response models defined in models.py
- All DynamoDB access via db.py helper only — never call boto3 directly from routes
- Decimal → float conversion always via float() before returning in response

## Tests
- pytest tests/ — must be 100% green before any PR
- Every new endpoint needs at least one happy-path and one error-path test

## How to Run Locally
```bash
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
```

## Confluence Requirements
FR-001: Product listing page with category filter
FR-002: Product detail page
NFR-001: p95 response time < 2 seconds
NFR-002: Mobile responsive frontend
