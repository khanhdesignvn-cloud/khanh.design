# Mindmap upgrade — approved scope and execution record

## Safety gates

Preflight: worktree clean at 7d4f040; process inspection found only production Wrangler runtime and this inspection in project paths, no independent editor/build worker. No database reset, production test writes, credential or Hermes configuration changes. Preserve Group.category, both official statuses, existing content/IDs, slideshow/download/Drive behavior. Never display original filenames; stored download filenames stay unchanged.

## Acceptance checklist (unchecked means incomplete; partial slices below)

- [x] 1. Global search over authorized input: project/category/line/product breadcrumbs, notes and positional codes; navigate result. Public live + fixture-browser verified; cross-project admin UI not separately exercised.
- [ ] 2. Smart filters: official status, missing attachments, overdue only with real explicit dates.
- [ ] 3. Server-authored append-only audit journal with actor/revision and safe display.
- [ ] 4. Version history with preview + explicit confirmed optimistic restore.
- [ ] 5. File roles and explicit current version, preserving old attachments.
- [ ] 6. Scoped revocable shares, server-side allowlist projection and protected file reads.
- [ ] 7. Customer feedback/approval per version, separate from the two official statuses.
- [ ] 8. Side-by-side version comparison with non-image fallback.
- [ ] 9. PDF + ZIP handover, safe filenames, bounded local-only file collection.
- [x] 10. Progress dashboard computed from current real data; verified on both live public shares.
- [ ] 11. Immutable product codes with collision-safe migration and server enforcement.
- [ ] 12. Daily backups, >=30 retained verified snapshots and isolated restore verification.
- [ ] 13. Owner/editor/client permissions enforced on every server action; no weak bootstrap credentials.
- [ ] 14. Controlled idempotent Drive current/selected sync preserving existing Drive files.

## Design constraints

Security/backup foundations precede richer UI. Additive schema only; legacy data remains readable. Share expiry/revocation and scopes must apply equally to metadata and file access. Restore is a new revision, never destructive history rewrite. New permissions fail closed, never hardcoded passwords. Backups must use SQLite online backup or a quiesced service snapshot (never an uncoordinated live WAL copy), integrity verification, private storage and non-destructive isolated restore exercises. This slice uses a brief stop/start of only khanh-design.service to capture D1/R2 consistently. Drive control must never delete existing remote files.

## Execution

## Verified local slice (2026-09-10)

Resumed existing changes at 7d4f040; re-read status/diff and modified files. No concurrent editor/build writer found; stopped only the previous worker's isolated Wrangler preview on 8795 before rebuilding. No production D1 writes/reset or Hermes changes.

- `NODE_OPTIONS=--max-old-space-size=640 npm test`: build succeeded; 25 tests passed, 0 failed.
- Python backup suite: 2 passed. Snapshot `/var/backups/khanh-design/snapshot-20260909T203848-2075188`: isolated restore verifies 8 SQLite databases, 62 state files, main revision 168 / hkm revision 10; manifest hashes match all 67 entries.
- Implemented search over authorized data, accent folding, project/category/line breadcrumbs, public design notes and positional codes; status and attached/missing filters; overview progress and result navigation.
- Public project API now uses an explicit nested allowlist and no-store headers. Unit tests inject internal metadata at every level and prove exclusion without altering stored data. Original attachment names remain in API/download metadata by design; UI must not display them. This is NOT complete scoped file authorization.
- Predeploy read-only production baseline: Farm 4 categories / 13 lines / 18 products; other project 9 groups / 57 items. Main 168, hkm 10.

Full checklist items 2, 6 and 12 remain partial: no overdue data/filter, no expiry/scoped file authorization, and not yet 30 historical snapshots. Audit/version history, file versions/roles, feedback, comparison, PDF/ZIP handover, immutable codes, richer permissions and controlled Drive sync remain unimplemented in this slice.

## Deployed and verified (2026-09-10)

- Feature commit `8f3069d` pushed to `origin/feat/cloudflare-project-manager`. Built output deployed in place to `/opt/khanh-design/releases/247ff8a/dist`; rsync checksum dry-run confirms no source/release differences (excluding `.dev.vars` and `.wrangler`). Secrets symlink preserved, runtime directory excluded. Previous dist rollback archive: `/tmp/khanh-design-pre-insights-dist.tar.gz` (not a long-term backup).
- Only `khanh-design.service` stopped/started for deployment; active/running afterward. Initial loopback connection refusals during startup recovered via bounded curl retries. No D1 reset or production test mutations; no Hermes services/config touched.
- Read-only pre/post comparison proves identical main/hkm payload SHA-256 and revisions (168/10). Farm stays 4 categories / 13 lines / 18 products, including rendered separate category/line/product nodes. Existing 100-year project stays 9 groups / 57 items.
- HTTPS live checks: `/admin`, `/100/`, `/khesanhfarm/`, both `/p/<token>` and matching `/api/project/<token>` return 200. Unknown token returns 404. Guest `/api/workspace` returns no projects. Public API response keys match the nested allowlist and Cache-Control is `private, no-store`.
- Live Farm share: `https://khanh.design/p/1f7102fc-3893-49bc-8d21-fc3eab494fc2`. Live legacy project share: `https://khanh.design/p/dd95800d-dccb-4982-9dc7-b9694ff106be`.
- Real Chromium against both actual HTTPS public shares: overview totals, positional-code search, result-to-detail navigation, missing-attachment and completion filters pass. Farm overview shows 2/18 complete and 18 missing attachments; 100-year project shows 5/57 complete and 50 missing attachments. These counts are live observations, not seeded fixtures. No page errors or mutation attempts.
- Nine browser regression tests pass against deployed HTTPS assets with intercepted fixture GETs only: one search/filter/navigation/mobile test, four item-detail tests and four showcase tests. They verify accent-folded notes/breadcrumbs, filename display privacy (text/alt/title/accessible names), PDF/Drive links, slideshow ordering, keyboard/focus/fullscreen, trusted mobile swipe and responsive bounds. Fixture results are not production data claims. Original filenames remain in API/download metadata, intentionally; no claim of removing that metadata or securing file reads by share scope.
- Live screenshot evidence inspected at `/tmp/mindmap-upgrade-evidence/farm-live-overview-{desktop,mobile}.png`; readable overview and no document horizontal overflow at 390px. Tabs intentionally scroll horizontally on mobile. Recaptured after asserting the status menu closed, avoiding its exit-animation screenshot artifact. JSON live-check evidence: `/tmp/mindmap-live-report.json`.
- Backup timer inspected active, daily schedule configured. Existing snapshot reverified: 8 databases, 62 state files, all 67 manifest entries match. Restore runs in a private temporary copy, never restores into production. No claim that 30 historical verified daily snapshots already exist.

### Still remaining / not claimed shipped

Overdue filtering and explicit dates; server-authored audit journal; version history/confirmed restore; attachment roles/current versions; expiring/scoped shares and protected file reads; customer feedback/approval; comparison; new PDF/ZIP handover exports; immutable codes; owner/editor/client authorization; controlled non-destructive current/selected Drive sync; accumulation and verification of at least 30 historical daily snapshots. Existing legacy report/Drive behavior is preserved, not upgraded into these requested features. Cross-project admin interactions still need a dedicated authenticated browser test.
