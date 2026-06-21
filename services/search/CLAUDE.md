# CLAUDE.md — Search Service (SVC-5)
## Owned DynamoDB Key Prefixes
- SEARCH# (index entries)
- May READ (not write) PRODUCT# and CATEGORY# items for search
## Phase 0: DynamoDB scan with filter expression
## Phase 2: Replace with OpenSearch when product count exceeds 500
## Confluence: FR-004
