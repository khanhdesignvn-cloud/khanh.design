import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const publicRoot = path.join(root, "public");

function read(relative) {
  return fs.readFileSync(path.join(publicRoot, relative), "utf8");
}

test("preserves the Khe Sanh brand deck under /100", () => {
  const html = read("100/index.html");
  assert.match(html, /100 NĂM CÀ PHÊ KHE SANH|100 năm cà phê Khe Sanh/i);
  assert.ok(fs.existsSync(path.join(publicRoot, "100/slide-config.json")));
});

test("preserves the Khe Sanh Farm wrapper under /khesanhfarm", () => {
  const html = read("khesanhfarm/index.html");
  assert.match(html, /Khe Sanh Farm/);
  assert.match(html, /khanhdesignvn-cloud\.github\.io\/khesanhfarm/);
});

test("legacy HTML does not reference missing local assets", () => {
  for (const relative of ["100/index.html", "khesanhfarm/index.html"]) {
    const html = read(relative);
    const base = path.dirname(path.join(publicRoot, relative));
    const refs = [...html.matchAll(/(?:src|href)=["']([^"'#?]+)["']/gi)]
      .map((match) => match[1])
      .filter((ref) => !/^(?:https?:|data:|mailto:|javascript:|\/)/i.test(ref));
    for (const ref of refs) {
      assert.ok(fs.existsSync(path.resolve(base, ref)), `${relative} misses ${ref}`);
    }
  }
});
