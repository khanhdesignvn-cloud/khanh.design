import assert from "node:assert/strict";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = fileURLToPath(new URL("..", import.meta.url));

async function readJavaScriptTree(directory) {
  const entries = await readdir(directory, { withFileTypes: true });
  const parts = await Promise.all(entries.map(async (entry) => {
    const target = path.join(directory, entry.name);
    if (entry.isDirectory()) return readJavaScriptTree(target);
    return entry.name.endsWith(".js") ? readFile(target, "utf8") : "";
  }));
  return parts.join("\n");
}

test("build contains development preview metadata", async () => {
  const serverBundle = await readJavaScriptTree(path.join(root, "dist/server"));
  assert.match(serverBundle, /codex-preview/);
  assert.match(serverBundle, /development/);
});
