# CLAUDE.md — Discount Coupon Service (SVC-6)
## Owned DynamoDB Key Prefixes
- PK: `COUPON#<CODE>` SK: `METADATA` (coupon definition: type, value, min_order, expires_at, max_uses, uses_count)
- PK: `COUPON#<CODE>` SK: `REDEMPTION#<user_id>` (per-user redemption record — enforces single use per user)
- PK: `COUPON#SESSION#<session_id>` SK: `APPLIED` (coupon currently attached to a cart session)
## FORBIDDEN Key Prefixes
- `PRODUCT#*` `CATEGORY#*` `CART#*` `ORDER#*` `USER#*` `SEARCH#*`
## Key Rules
- Coupon codes are normalised to UPPERCASE on read and write.
- Discount types: `percentage` (0–100, applied to order_total) and `fixed` (£ off, capped at order_total). Discount never exceeds the order total; final_total floors at 0.
- All money is stored as `Decimal` and returned rounded to 2 dp (half-up).
- Validation enforced on validate + apply: coupon exists & active, not expired (`expires_at` ISO `YYYY-MM-DD`), `order_total >= min_order`, global `uses_count < max_uses` (`max_uses == 0` means unlimited), and single use per user.
- `POST /v1/coupons/validate` is stateless — it never consumes a coupon.
- `POST /v1/cart/{session_id}/coupon` consumes a coupon: it atomically increments `uses_count` (conditional on `< max_uses`) and writes `REDEMPTION#<user_id>` (conditional on absence). `DELETE` reverses both. This service does NOT write `CART#` keys — the session linkage lives under the owned `COUPON#SESSION#` prefix, and `order_total` is supplied by the caller.
## Endpoints (port 8006)
- `GET  /v1/health`
- `POST /v1/coupons/validate`
- `POST /v1/cart/{session_id}/coupon`
- `DELETE /v1/cart/{session_id}/coupon`
- `POST /v1/coupons`
## Confluence: FR-006
