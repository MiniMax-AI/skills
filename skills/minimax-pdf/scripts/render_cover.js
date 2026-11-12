#!/usr/bin/env node
/**
 * render_cover.js — Render cover.html → cover.pdf via Playwright.
 *
 * Usage:
 *   node render_cover.js --input cover.html --out cover.pdf
 *   node render_cover.js --input cover.html --out cover.pdf --wait 1200
 *   node render_cover.js --check-playwright
 *
 * Exit codes: 0 success, 1 bad args, 2 dependency missing, 3 render error
 */

const path = require("path");
const fs   = require("fs");

function usage() {
  console.error("Usage: node render_cover.js --input <file.html> --out <file.pdf> [--wait <ms>]");
  process.exit(1);
}

// ── Arg parsing ────────────────────────────────────────────────────────────────
const args = process.argv.slice(2);
let inputFile = null, outFile = null, waitMs = 800;
const checkPlaywright = args.includes("--check-playwright");

for (let i = 0; i < args.length; i++) {
  if (args[i] === "--input" && args[i + 1]) { inputFile = args[++i]; }
  else if (args[i] === "--out"   && args[i + 1]) { outFile   = args[++i]; }
  else if (args[i] === "--wait"  && args[i + 1]) { waitMs    = parseInt(args[++i], 10); }
}

if (!checkPlaywright && (!inputFile || !outFile)) usage();
if (!checkPlaywright && !fs.existsSync(inputFile)) {
  console.error(JSON.stringify({ status: "error", error: `File not found: ${inputFile}` }));
  process.exit(1);
}

// ── Playwright loader (tolerates local, nested, and global npm installs) ───────
function tryRequirePlaywright(root) {
  for (const candidate of [
    path.join(root, "playwright"),
    path.join(root, "@playwright", "mcp", "node_modules", "playwright"),
  ]) {
    try { return require(candidate); } catch (_) {}
  }
  try {
    const mcpPackage = require.resolve("@playwright/mcp/package.json", { paths: [root] });
    const nested = require.resolve("playwright", { paths: [path.dirname(mcpPackage)] });
    return require(nested);
  } catch (_) {}
  return null;
}

function loadPlaywright() {
  const { execSync } = require("child_process");
  try { return require("playwright"); } catch (_) {}
  const roots = new Set([
    path.resolve(process.cwd(), "node_modules"),
    path.resolve(__dirname, "..", "node_modules"),
    path.resolve(__dirname, "..", "..", "node_modules"),
  ]);
  for (const npmArgs of ["npm root", "npm root -g"]) {
    try {
      const root = execSync(npmArgs, { stdio: ["ignore", "pipe", "ignore"], shell: true })
        .toString()
        .trim();
      if (root) roots.add(root);
    } catch (_) {}
  }
  for (const root of roots) {
    const playwright = tryRequirePlaywright(root);
    if (playwright !== null) return playwright;
  }
  console.error(JSON.stringify({
    status: "error",
    error: "playwright not found",
    hint: "Run: npm install -g playwright && npx playwright install chromium"
  }));
  process.exit(2);
}

if (checkPlaywright) {
  loadPlaywright();
  process.exit(0);
}

// ── Main ───────────────────────────────────────────────────────────────────────
(async () => {
  const { chromium } = loadPlaywright();

  let browser;
  try {
    browser = await chromium.launch();
  } catch (e) {
    // Chromium binary missing — try installing
    const { spawnSync } = require("child_process");
    const r = spawnSync("npx", ["playwright", "install", "chromium"], { stdio: "inherit", shell: true });
    if (r.status !== 0) {
      console.error(JSON.stringify({
        status: "error",
        error: "Chromium not installed and auto-install failed",
        hint: "Run: npx playwright install chromium"
      }));
      process.exit(2);
    }
    browser = await chromium.launch();
  }

  try {
    const page = await browser.newPage();
    const fileUrl = "file://" + path.resolve(inputFile);
    await page.goto(fileUrl);
    await page.waitForTimeout(waitMs);   // let CSS + any JS settle

    await page.pdf({
      path:            outFile,
      width:           "794px",
      height:          "1123px",
      printBackground: true,
    });

    await browser.close();

    // Basic sanity: output file must exist and be > 5 KB
    const stat = fs.statSync(outFile);
    if (stat.size < 5000) {
      console.error(JSON.stringify({
        status: "error",
        error: "Output PDF is suspiciously small — cover may be blank",
        hint:  "Check cover.html for render errors"
      }));
      process.exit(3);
    }

    console.log(JSON.stringify({
      status: "ok",
      out:    outFile,
      size_kb: Math.round(stat.size / 1024),
    }));

  } catch (e) {
    if (browser) await browser.close().catch(() => {});
    console.error(JSON.stringify({ status: "error", error: String(e) }));
    process.exit(3);
  }
})();
