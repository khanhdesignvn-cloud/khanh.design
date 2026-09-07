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
  server: { middlewareMode: true },
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
