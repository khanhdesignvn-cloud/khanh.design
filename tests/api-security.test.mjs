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

test("production administration is password-session only", async () => {
  const source = await readFile(path.join(root, "app/admin.ts"), "utf8");
  assert.doesNotMatch(source, /chatgpt-auth|getChatGPTUser|ADMIN_EMAILS/);
  assert.match(source, /validSession/);
});

test("accepts only declared media whose bytes match its MIME type", async () => {
  const { validateUpload } = await vite.ssrLoadModule("/app/upload-validation.ts");
  const jpeg = new Uint8Array([0xff, 0xd8, 0xff, 0xdb]);
  const png = new Uint8Array([0x89, 0x50, 0x4e, 0x47, 0x0d, 0x0a, 0x1a, 0x0a]);
  const pdf = new TextEncoder().encode("%PDF-1.7\n");

  assert.equal(validateUpload("image/jpeg", jpeg), null);
  assert.equal(validateUpload("image/png", png), null);
  assert.equal(validateUpload("application/pdf", pdf), null);
  assert.match(validateUpload("image/jpeg", pdf), /không khớp/i);
  assert.match(validateUpload("text/html", new TextEncoder().encode("<html>")), /JPG, PNG, WebP, GIF hoặc PDF/);
});

test("rejects malformed WebP and GIF signatures", async () => {
  const { validateUpload } = await vite.ssrLoadModule("/app/upload-validation.ts");
  assert.match(validateUpload("image/webp", new TextEncoder().encode("RIFFxxxxNOPE")), /không khớp/i);
  assert.match(validateUpload("image/gif", new TextEncoder().encode("GIF00a")), /không khớp/i);
});

test("rejects unsafe password-hash parameters", async () => {
  const { parsePasswordHash } = await vite.ssrLoadModule("/app/password-hash.ts");
  const digest = "ab".repeat(32);
  assert.equal(parsePasswordHash(`1:${"ab".repeat(16)}:${digest}`), null);
  assert.equal(parsePasswordHash(`120000:${"ab".repeat(8)}:${digest}`), null);
  assert.equal(parsePasswordHash(`120000:${"ab".repeat(16)}:${"ab".repeat(8)}`), null);
  assert.equal(parsePasswordHash(`120000:${"ab".repeat(16)}:${digest}`)?.rounds, 120000);
});

test("bounded body reader stops chunked requests before buffering excess data", async () => {
  const { readBodyLimited } = await vite.ssrLoadModule("/app/request-limits.ts");
  const request = new Request("https://example.test/api", {
    method: "POST",
    body: new ReadableStream({
      start(controller) {
        controller.enqueue(new Uint8Array(1500));
        controller.enqueue(new Uint8Array(1500));
        controller.close();
      },
    }),
    duplex: "half",
  });
  await assert.rejects(() => readBodyLimited(request, 2048), /too large/i);
});

test("logout revokes server-side session state", async () => {
  const source = await readFile(path.join(root, "app/api/auth/logout/route.ts"), "utf8");
  const migration = await readFile(path.join(root, "drizzle/0002_admin_sessions.sql"), "utf8");
  assert.match(source, /revokeSession/);
  assert.match(migration, /CREATE TABLE.*admin_sessions/is);
});
