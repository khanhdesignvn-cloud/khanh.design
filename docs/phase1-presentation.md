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
- [x] Production backup and isolated restore verified.
- [x] Metadata-only assignment of current real design and Farm projects.
- [x] In-place deployment, assets identical, secrets/runtime preserved.
- [x] Real HTTPS shares on desktop/mobile, fixture course (not stored), live image download/Drive/slideshow and Farm hierarchy verified.
- [x] Application and verification commit `3dd7fc9` pushed; `git ls-remote` matched local HEAD. Final documentation-only closeout follows (does not change deployed build).

## Operations

Source branch: `feat/cloudflare-project-manager`. Deploy only to existing `/opt/khanh-design/releases/247ff8a/dist`, excluding `.dev.vars` and `.wrangler`, restarting only `khanh-design.service`. No Hermes changes.

Migration: `scripts/set-project-presentations.py DB UNIQUE_BACKUP EXPECTED_REVISION '{"khesanh":"design","3cc585ac-3cdb-4b70-9e71-cc8369b66499":"catalog"}'`. Read current full database payload first; never write a public projection or reseed. Inspect and compare all stored fields after migration, permitting only those two metadata fields and main revision increment. Preflight: main 168, hkm 10; design 9 groups/57 items; Farm 4 categories/13 lines/18 products.

Rollback: stop only app service, restore archived old dist with rsync excluding `.dev.vars`/`.wrangler`, start app, check loopback and HTTPS. Additive presentation metadata is harmless to the prior app; do not restore the whole live DB over concurrent edits. Database backup is for verified recovery, not a production test fixture.

Evidence on host: `/tmp/phase1-evidence/`, `/tmp/phase1-test-rerun.log`, `/tmp/phase1-browser-built-final.log`. Fixtures are not real user content. Actual image byte download is tested separately from the Drive action: TẢI FILE GỐC opens the stored Google Drive URL, not a new ZIP/download backend.

Other backlog in `overnight-mindmap-upgrade.md` remains outside this slice.

## Resumed delivery verification — 2026-09-10

The interrupted worker had **already deployed application commit `248e9da`** and assigned metadata at revision 168→169. It had not pushed: origin was still `6c2040c`. This continuation did not migrate again, reset data, restart production or redeploy unchanged application code.

Fresh evidence:

- All 79 original built files matched the release byte-for-byte before rebuilding; all 11 HTTPS `/assets/*` responses matched local SHA-256. `.dev.vars` remains a symlink and `.wrangler` exists. Evidence: `/tmp/phase1-evidence/final-asset-checks.json`.
- Fresh `NODE_OPTIONS=--max-old-space-size=640 npm test`: **28/28**, zero failures. The old isolated staging processes were stopped first; production was untouched. Log: `final-build-tests.log` in the evidence directory.
- The fresh rebuild has identical client assets. Three server files differ only in Vinext-generated build IDs/draft/prerender secrets, verified by exact comparison after normalizing only those fields. No app-source difference; no unnecessary redeploy. `rebuild-equivalence.json` records this distinction.
- **11/11 Chromium fixture tests** rerun against deployed HTTPS assets (`test_phase1_browser`, `test_item_detail_browser`, `test_showcase_browser`, `test_mindmap_insights_browser`), including desktop/mobile design/course/catalog, scroll/pan/zoom, filename privacy and slideshow regressions. `final-browser-tests.log`.
- **3/3 Python migration/backup tests** rerun on temporary data, not production.
- `tests/verify_phase1_live.py`: both real shares at 1440 and 390px, actual intro/progress, remembered tab/group/search/attachment filter/root collapse on reload, clickable reset breadcrumb, loaded visible gallery images, clean client empty state, no document overflow, zero browser errors/writes. Also guest workspace empty, invalid share 404, admin/legacy route HTTP200. `https-live.json`, `final-live-tests.log`, `live-design-{1440,390}.png`, `live-catalog-{1440,390}.png`.
- `FARM_BASE=https://khanh.design ... tests/test_category_browser.py`: real four-column root/category/line/product tree, **4/13/18**, independent collapse and table/gallery/report desktop/mobile passed. Screenshots `/tmp/farm-live-map.png`, `/tmp/farm-live-mobile.png`.
- `tests/verify_item_detail_live.py`: live four-image item slideshow, fullscreen, touch swipe, focus return, filename hiding, exact Drive folder link and downloaded image **696521 bytes**, SHA-256 `432d85d4266ec6c20e86cbf62aad9e62fcf9ee65ae57687b905b702223d419a9`. Evidence `/tmp/filename-privacy-evidence/live/verification.json` and screenshots. Fixed only a flaky test's 650ms hover sleep: polling now waits for the actual gradient endpoint; the application needed no change. Phase1 screenshots now wait for visible lazy images rather than recording loading placeholders.
- Read-only SQLite integrity is `ok`; exactly **2 projects**, main revision **176**, HKM **10**. Comparing full current payload to the predeployment snapshot after excluding only presentation/updatedAt shows **all other main data identical**, and HKM identical. `final-data-checks.json`. No course project created.
- Existing backup `/var/backups/khanh-design/snapshot-20260910T010943-2101544/restore-verification.json` records isolated verification of **8 databases / 64 files**, workspace revisions main168/HKM10. No new restore over production.

Current real progress: design **5/57**, 9 groups; Farm **2/18**, 13 lines in 4 categories. Both server metadata dates are `2026-09-10T01:10:37.508Z` (UI intentionally displays the date). The design subtitle still contains user-stored legacy text “61 hạng mục / 8 nhóm”; it was deliberately not rewritten as part of this UX-only completion. Actual progress/counts derive from current data. Course is a presentation fixture, not an LMS. Drive action opens the stored folder; it is not a ZIP exporter. Browser verification is Chromium desktop/mobile emulation, not a physical Safari/iOS run.
