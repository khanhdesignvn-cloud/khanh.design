# Item detail viewer and original-file action

## Scope

- Item Drive anchor reads **TẢI FILE GỐC**, with a download icon, teal/blue gradient, shifted hover gradient, pale outline, lift and reduced-motion support. It opens the exact stored Drive URL in a new tab. This is the approved open-Drive behavior, not a ZIP download backend.
- Both admin and public detail image buttons snapshot only that item's image attachments into `ShowcaseSlideshow` with `enhanced` enabled. PDFs keep their existing preview and Drive attachments keep their separate links.
- Enhanced mode adds thumbnails, 100–400% zoom/reset and original-byte image download. Existing previous/next, wraparound, arrows, Escape, focus restoration, fullscreen and mobile swipe are reused. Swiping while zoomed does not navigate away.
- The global Showcase still provides its original continuous image sequence across items. It does not enable the extra item toolbar. The shared counter now explicitly uses a light text color (global footer rules previously made it near-black).
- No schema, seed, DB, original artwork or filename changes.

## Verification

```sh
NODE_OPTIONS=--max-old-space-size=640 npm test
# Separate built-assets staging, isolated persistence, no live DB seed:
node node_modules/wrangler/bin/wrangler.js dev --local --config dist/server/wrangler.json --persist-to /tmp/item-detail-staging-state --port 8795 --ip 127.0.0.1 --log-level warn
PYTHONPATH=tests python -m unittest test_item_detail_browser test_showcase_browser -v
ITEM_BASE_URL=https://khanh.design SHOWCASE_BASE_URL=https://khanh.design PYTHONPATH=tests python -m unittest test_item_detail_browser test_showcase_browser -v
python tests/verify_item_detail_live.py
FARM_BASE=https://khanh.design python tests/test_category_browser.py
```

Executed results: bounded production build + **22 Node tests passed**; **7 Chromium tests passed** on staging and again on HTTPS live. Item tests first failed on the old plain Drive link / single-image lightbox. A separate failing contrast assertion caught the dark counter.

Real live test used “Logo chính thức”: 4 original images, exact selected-image start, thumbnail count, zoom/reset, fullscreen, keyboard close/focus return, mobile trusted swipe, actual Drive new-tab navigation. Downloaded `Logo 100 v02 c@100.jpg`: **696521 bytes**, SHA256 `432d85d4266ec6c20e86cbf62aad9e62fcf9ee65ae57687b905b702223d419a9`, byte-identical to the existing image endpoint. No app mutation attempts or browser errors.

Four-level Farm live regression passed: 4 category /13 line /18 product nodes, four separate columns, independent root/category/line collapse, details, table, showcase, report and desktop/mobile.

Artifacts on deployment host: `/tmp/item-detail-evidence/` (build and browser logs); `live/verification.json`, `live/drive-desktop.png`, `live/slideshow-desktop.png`, `live/slideshow-mobile.png`, `live/detail-mobile.png`. Fixture captures are test fixtures, not user artwork.

## Deployment and rollback

Deployed built assets in-place to `/opt/khanh-design/releases/247ff8a/dist`, preserving `.dev.vars` and `.wrangler`, restarting only `khanh-design.service`. Verified service active and public HTTPS 200. Rollback archive: `/tmp/item-detail-evidence/rollback-dist-1a28447.tar.gz`. If rollback is needed, stop the app service, extract archive into a temporary directory, rsync its `dist/` in-place with both exclusions, restart and verify HTTPS. Do not restore workspace data.

Live data changed concurrently during this UI work: main revision 161→166, limited to one Farm product name and two Farm statuses. This work issued no workspace writes and intentionally did **not** revert those external edits. Legacy project and HKM payloads remained byte-identical; Farm hierarchy IDs and attachment content remained intact. Before/after read-only snapshots and changed-field paths remain local under the evidence directory, not in git.
