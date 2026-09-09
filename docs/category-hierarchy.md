# Khe Sanh Farm — approved four-level hierarchy

Project → category → product line → product. `Group.category?: string` is optional; `Group.name` is the product-line name. Category parents are derived from this metadata and rendered as separate connected nodes, not concatenated labels. Existing groups without metadata still render the legacy three-level map. Category identity is the exact category name; renaming a category updates all member lines, and renaming to an existing category merges those branches. Empty categories are not persisted independently: create a line and enter its category to create a new branch.

Root, each category and each line have independent local collapse state. Leaf status, notes and attachments remain on the same original Item objects/IDs. Table, showcase, report and item group-picker display category / line breadcrumbs. Category controls allow rename and line creation. The line editor can assign a new/existing category or clear it. Moving a line onto a line in another category adopts the destination category, including keyboard up/down; moving a product adopts its destination line. Category nodes themselves are not draggable.

`layoutHierarchy` calculates spans without mutating data; map fit reads the actual canvas width. Category strings are validated at the workspace write boundary. Autosave keeps the existing revision compare-and-swap mechanism.

## Verification

- `NODE_OPTIONS=--max-old-space-size=640 npm test`: production build + Node suite.
- `python tests/test_category_browser.py`: built assets at isolated `127.0.0.1:8795`, copied local DB and independently generated staging session secret. Requires the migrated baseline; admin tests intentionally change only staging. Covers separate node coordinates/counts, independent collapse, public detail, all four views, desktop/mobile, real category rename/line creation/pointer drag, reload persistence, HTTP 400 invalid category and 409 stale revision, legacy project UI, unchanged original leaves and unrelated projects.
- `FARM_BASE=https://khanh.design python tests/test_category_browser.py`: public read-only live checks only.
- Plain `tsc --noEmit` currently lacks Cloudflare workers/D1/R2 type declarations (pre-existing); Vinext production build succeeds.

## Data/deployment

`python scripts/migrate-farm-categories.py DB BACKUP_DIR EXPECTED_REVISION` creates an integrity-checked SQLite backup, locks the DB with BEGIN IMMEDIATE, rechecks the revision, and only splits the 13 approved Farm group names. It asserts 18 products and unchanged item bodies/IDs and other projects, then increments revision. It refuses a stale revision or a second migration. Never reseed/delete the workspace.

Deploy in place at `/opt/khanh-design/releases/247ff8a/dist`, excluding `.dev.vars` and `.wrangler`. Snapshot existing dist before replacing it; restart only `khanh-design.service`. Rollback code via the saved dist archive, with the same exclusions. Metadata is backward compatible, so an emergency code rollback does not require restoring an old entire database. If data rollback is needed, first stop writes, inspect current revision and any subsequent user edits, then reverse only Farm category/name metadata transactionally; do not overwrite other projects with an old backup.
