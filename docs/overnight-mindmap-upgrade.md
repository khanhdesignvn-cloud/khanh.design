# Mindmap upgrade — approved scope and execution record

## Safety gates

Preflight: worktree clean at 7d4f040; process inspection found only production Wrangler runtime and this inspection in project paths, no independent editor/build worker. No database reset, production test writes, credential or Hermes configuration changes. Preserve Group.category, both official statuses, existing content/IDs, slideshow/download/Drive behavior. Never display original filenames; stored download filenames stay unchanged.

## Acceptance checklist (unchecked means NOT shipped)

- [ ] 1. Global search: project/category/line/product breadcrumbs, notes and codes; navigate result.
- [ ] 2. Smart filters: official status, missing attachments, overdue only with real explicit dates.
- [ ] 3. Server-authored append-only audit journal with actor/revision and safe display.
- [ ] 4. Version history with preview + explicit confirmed optimistic restore.
- [ ] 5. File roles and explicit current version, preserving old attachments.
- [ ] 6. Scoped revocable shares, server-side allowlist projection and protected file reads.
- [ ] 7. Customer feedback/approval per version, separate from the two official statuses.
- [ ] 8. Side-by-side version comparison with non-image fallback.
- [ ] 9. PDF + ZIP handover, safe filenames, bounded local-only file collection.
- [ ] 10. Progress dashboard computed from current real data.
- [ ] 11. Immutable product codes with collision-safe migration and server enforcement.
- [ ] 12. Daily backups, >=30 retained verified snapshots and isolated restore verification.
- [ ] 13. Owner/editor/client permissions enforced on every server action; no weak bootstrap credentials.
- [ ] 14. Controlled idempotent Drive current/selected sync preserving existing Drive files.

## Design constraints

Security/backup foundations precede richer UI. Additive schema only; legacy data remains readable. Share expiry/revocation and scopes must apply equally to metadata and file access. Restore is a new revision, never destructive history rewrite. New permissions fail closed, never hardcoded passwords. Backups use SQLite online backup (not live WAL file copies), integrity verification, private storage and non-destructive isolated restore exercises. Drive control must never delete existing remote files.

## Execution

## Verified local slice (2026-09-10)

Resumed existing changes at 7d4f040; re-read status/diff and modified files. No concurrent editor/build writer found; stopped only the previous worker's isolated Wrangler preview on 8795 before rebuilding. No production D1 writes/reset or Hermes changes.

- `NODE_OPTIONS=--max-old-space-size=640 npm test`: build succeeded; 25 tests passed, 0 failed.
- Python backup suite: 2 passed. Snapshot `/var/backups/khanh-design/snapshot-20260909T203848-2075188`: isolated restore verifies 8 SQLite databases, 62 state files, main revision 168 / hkm revision 10; manifest hashes match all 67 entries.
- Implemented search over authorized data, accent folding, project/category/line breadcrumbs, public design notes and positional codes; status and attached/missing filters; overview progress and result navigation.
- Public project API now uses an explicit nested allowlist and no-store headers. Unit tests inject internal metadata at every level and prove exclusion without altering stored data. Original attachment names remain in API/download metadata by design; UI must not display them. This is NOT complete scoped file authorization.
- Predeploy read-only production baseline: Farm 4 categories / 13 lines / 18 products; other project 9 groups / 57 items. Main 168, hkm 10.

Deployment and live/browser verification will be recorded below after execution. Full checklist items 2, 6 and 12 remain partial: no overdue data/filter, no expiry/scoped file authorization, and not yet 30 historical snapshots. Audit/version history, file versions/roles, feedback, comparison, PDF/ZIP handover, immutable codes, richer permissions and controlled Drive sync remain unimplemented in this slice.
