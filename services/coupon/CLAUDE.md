# CLAUDE.md — Discount Coupon Service (SVC-6)
## Owned DynamoDB Key Prefixes
- PK: `COUPON#<CODE>` SK: `METADATA` (coupon definition: discount_type, discount_value, status, created_at, redeemed_at, redeemed_by_order_id)
## FORBIDDEN Key Prefixes
- `PRODUCT#*` `CATEGORY#*` `CART#*` `ORDER#*` `USER#*` `SEARCH#*`
## Key Rules
- Coupon codes are normalised to UPPERCASE on read and write.
- Discount types: `percentage` (applied to cart_total) and `fixed` (£ off, capped at cart_total per AC-004). Final total floors at £0.
- Each coupon is single-use globally: status transitions ACTIVE → REDEEMED exactly once.
- Atomic redemption uses a DynamoDB conditional write (ConditionExpression: `status = ACTIVE`) to prevent race conditions (AC-010).
- `POST /v1/coupons/validate` is stateless — never changes status. Returns `{valid: false, error: "..."}` on failure.
- `POST /v1/coupons/redeem` is called on order placement and atomically sets status to REDEEMED.
- Error messages are exact per FR-006: "Invalid coupon code." (AC-012) and "This coupon has already been used." (AC-011).
- All money rounded to 2 dp (half-up).
- Coupons are seeded via script (no admin API in Phase 2 — deferred per FR-006 out-of-scope).
## Data Model (DynamoDB single-table retail-platform)
- status: "ACTIVE" | "REDEEMED"
- discount_type: "percentage" | "fixed"
- discount_value: Decimal
- created_at: Unix timestamp
- redeemed_at: Unix timestamp (set on redemption)
- redeemed_by_order_id: str (set on redemption)
## Endpoints (port 8006)
- `GET  /v1/health`
- `POST /v1/coupons/validate`   body: {code, cart_total}
- `POST /v1/coupons/redeem`     body: {code, order_id}
## Confluence: FR-006
