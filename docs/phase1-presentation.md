# Phase 1 — project presentation and navigation

## Approved slice

- Explicit optional `design | course | catalog`, backwards-compatible design default, admin selector. No name inference or fabricated course project.
- Public summary, progress and server-authored update timestamp; explicit public projection.
- Per-type table/gallery/report labels; project/category/group breadcrumbs and group selection.
- Project/access-surface-scoped view, search, status/attachment/group filters, collapse, scroll and map pan/zoom memory.
- Read-only empty gallery copy. Existing filename privacy, item/global slideshows, image download, Drive links and four-level Farm hierarchy preserved.

## Acceptance gates

- [x] Bounded production build and 28 Node tests passed (heap 640 MB).
- [x] Three Python migration/backup tests passed. Migration refuses stale revisions and preserves every field except presentation/updatedAt.
- [x] Eleven Chromium tests passed against final built staging assets, including desktop/mobile design/course/catalog fixtures and navigation restoration.
- [ ] Production backup and isolated restore verified.
- [ ] Metadata-only assignment of current real design and Farm projects.
- [ ] In-place deployment, assets identical, secrets/runtime preserved.
- [ ] Real HTTPS shares on desktop/mobile, fixture course (not stored), live image download/Drive/slideshow and Farm hierarchy verified.
- [ ] Commit pushed and remote verified.

## Operations

Source branch: `feat/cloudflare-project-manager`. Deploy only to existing `/opt/khanh-design/releases/247ff8a/dist`, excluding `.dev.vars` and `.wrangler`, restarting only `khanh-design.service`. No Hermes changes.

Migration: `scripts/set-project-presentations.py DB UNIQUE_BACKUP EXPECTED_REVISION '{"khesanh":"design","3cc585ac-3cdb-4b70-9e71-cc8369b66499":"catalog"}'`. Read current full database payload first; never write a public projection or reseed. Inspect and compare all stored fields after migration, permitting only those two metadata fields and main revision increment. Preflight: main 168, hkm 10; design 9 groups/57 items; Farm 4 categories/13 lines/18 products.

Rollback: stop only app service, restore archived old dist with rsync excluding `.dev.vars`/`.wrangler`, start app, check loopback and HTTPS. Additive presentation metadata is harmless to the prior app; do not restore the whole live DB over concurrent edits. Database backup is for verified recovery, not a production test fixture.

Evidence on host: `/tmp/phase1-evidence/`, `/tmp/phase1-test-rerun.log`, `/tmp/phase1-browser-built-final.log`. Fixtures are not real user content. Actual image byte download is tested separately from the Drive action: TẢI FILE GỐC opens the stored Google Drive URL, not a new ZIP/download backend.

Other backlog in `overnight-mindmap-upgrade.md` remains outside this slice.
