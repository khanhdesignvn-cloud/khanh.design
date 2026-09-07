import assert from "node:assert/strict";
import { readFile } from "node:fs/promises";
import path from "node:path";
import test, { after } from "node:test";
import { fileURLToPath } from "node:url";
import { createServer } from "vite";

const root = fileURLToPath(new URL("..", import.meta.url));
const vite = await createServer({
  appType: "custom",
  configFile: false,
  root,
  resolve: { alias: { "@": root } },
  server: { middlewareMode: true, hmr: false },
});
after(async () => vite.close());

test("deployment config accepts real Cloudflare resource identifiers", async () => {
  const source = await readFile(path.join(root, "vite.config.ts"), "utf8");
  assert.match(source, /D1_DATABASE_ID/);
  assert.match(source, /D1_DATABASE_NAME/);
  assert.match(source, /R2_BUCKET_NAME/);
});

test("security headers prevent framing, sniffing and permission abuse", async () => {
  const { withSecurityHeaders } = await vite.ssrLoadModule("/app/security-headers.ts");
  const response = withSecurityHeaders(new Response("ok"));
  assert.equal(response.headers.get("x-content-type-options"), "nosniff");
  assert.equal(response.headers.get("x-frame-options"), "DENY");
  assert.equal(response.headers.get("referrer-policy"), "strict-origin-when-cross-origin");
  assert.match(response.headers.get("permissions-policy") ?? "", /camera=\(\)/);
});
