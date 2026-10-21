import assert from "node:assert/strict";
import { access, readFile } from "node:fs/promises";
import path from "node:path";
import test from "node:test";
import { fileURLToPath } from "node:url";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const read = (relativePath) => readFile(path.join(root, relativePath), "utf8");

function rgb(hex) {
  const value = hex.replace("#", "");
  return [0, 2, 4].map((offset) => parseInt(value.slice(offset, offset + 2), 16) / 255)
    .map((channel) => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4);
}

function contrast(first, second) {
  const luminance = (hex) => {
    const [r, g, b] = rgb(hex);
    return 0.2126 * r + 0.7152 * g + 0.0722 * b;
  };
  const values = [luminance(first), luminance(second)].sort((a, b) => b - a);
  return (values[0] + 0.05) / (values[1] + 0.05);
}

test("Vercel is configured to serve the public static site output", async () => {
  const config = JSON.parse(await read("vercel.json"));
  assert.equal(config.outputDirectory, "public");
  assert.equal(config.cleanUrls, true);
  assert.ok(Array.isArray(config.headers));
  const headers = config.headers.flatMap((item) => item.headers);
  assert.ok(headers.some((item) => item.key === "X-Content-Type-Options" && item.value === "nosniff"));
  assert.ok(headers.some((item) => item.key === "Content-Security-Policy" && item.value.includes("default-src 'self'")));
  assert.ok(headers.some((item) => item.key === "Referrer-Policy"));
  await access(path.join(root, config.outputDirectory, "index.html"));
});

test("landing page has a clear page title, description, single primary heading and local assets", async () => {
  const html = await read("public/index.html");
  assert.match(html, /<html lang="en">/);
  assert.match(html, /<title>AI Study Coach — Make study time count<\/title>/);
  assert.match(html, /<meta name="description" content="[^"]{40,}">/);
  assert.equal((html.match(/<h1(?:\s|>)/g) || []).length, 1);
  assert.match(html, /<h1>Make study time <span>count\.<\/span><\/h1>/);
  assert.match(html, /href="\/styles\.css"/);
  assert.match(html, /src="\/site\.js" defer/);
  assert.match(html, /href="\/favicon\.svg"/);
  for (const asset of ["public/styles.css", "public/site.js", "public/favicon.svg", "public/robots.txt", "public/sitemap.xml"]) {
    await access(path.join(root, asset));
  }
});

test("navigation fragments resolve and key controls are accessible", async () => {
  const html = await read("public/index.html");
  const ids = new Set([...html.matchAll(/\bid="([^"]+)"/g)].map((match) => match[1]));
  const fragments = [...html.matchAll(/\bhref="#([^"]+)"/g)].map((match) => match[1]);
  for (const fragment of fragments) assert.ok(ids.has(fragment), "Missing target #" + fragment);
  assert.match(html, /class="skip-link" href="#main"/);
  assert.match(html, /aria-label="Main navigation"/);
  assert.match(html, /aria-controls="primary-nav" aria-expanded="false"/);
  assert.match(html, /id="main"/);
  assert.match(await read("public/site.js"), /event\.key === "Escape"/);
  assert.match(await read("public/site.js"), /setAttribute\("aria-expanded"/);
});

test("landing page links directly to the working browser app", async () => {
  const html = await read("public/index.html");
  for (const match of html.matchAll(/<a\b([^>]*target="_blank"[^>]*)>/g)) {
    assert.match(match[1], /\brel="noreferrer"/, "Unsafe external link: " + match[0]);
  }
  assert.match(html, /href="\/app\/">Launch the web app/);
  assert.match(html, /href="\/app\/">Open AI Study Coach/);
  assert.match(html, /The web edition stores your activity in this browser/);
  assert.doesNotMatch(html, /href="(?:#|javascript:)"\s*>\s*(?:Launch|Open|Start) app/i);
});

test("the generated browser app includes notes, planning, quizzes, and progress", async () => {
  const html = await read("public/app/index.html");
  assert.match(html, /AI Study Coach — Browser App/);
  assert.match(html, /id="save-note-btn"/);
  assert.match(html, /id="notes-history"/);
  assert.match(html, /id="use-for-plan-btn"/);
  assert.match(html, /id="quiz-note-select"/);
  assert.match(html, /id="notes-count"/);
  assert.match(html, /local storage/);
  const browserScript = await read("public/app/app.js");
  assert.match(browserScript, /Browser workspace ready/);
  assert.match(browserScript, /History is saved in this browser/);
  assert.match(browserScript, /browser storage could not save/i);
  assert.doesNotMatch(browserScript, /Connected to Anna|Connecting to Anna|Anna storage could not save|saved with this Anna app/i);
  for (const asset of [
    "public/app/app.js",
    "public/app/style.css",
    "public/app/katex.min.css",
    "public/app/pdf.worker.min.mjs",
    "public/app/fonts/KaTeX_Main-Regular.woff2",
  ]) await access(path.join(root, asset));
});
test("core typography and text contrast meet accessible minimums", async () => {
  const css = await read("public/styles.css");
  const tokens = Object.fromEntries([...css.matchAll(/(--[\w-]+):\s*(#[0-9a-fA-F]{6})/g)].map((match) => [match[1], match[2]]));
  assert.ok(contrast(tokens["--muted"], tokens["--surface"]) >= 4.5, "Muted text should meet WCAG AA contrast on white");
  assert.ok(contrast(tokens["--green"], tokens["--surface"]) >= 4.5, "Primary green text should meet WCAG AA contrast on white");
  assert.match(css, /body\s*\{[^}]*font-size:\s*16px/s);
  assert.match(css, /:focus-visible/);
  assert.match(css, /@media \(max-width: 760px\)/);
  assert.match(css, /@media \(max-width: 480px\)/);
  assert.match(css, /prefers-reduced-motion: reduce/);
});

test("deployment is self-contained and does not depend on third-party font or script CDNs", async () => {
  const html = await read("public/index.html");
  const css = await read("public/styles.css");
  const js = await read("public/site.js");
  assert.doesNotMatch(html, /<script[^>]+src="https?:\/\//i);
  assert.doesNotMatch(html, /<link[^>]+href="https?:\/\/[^"]+\.css"/i);
  assert.doesNotMatch(css, /fonts\.googleapis\.com|fonts\.gstatic\.com|unpkg\.com|jsdelivr\.net/i);
  assert.doesNotMatch(js, /\bfetch\s*\(|\bXMLHttpRequest\b|gtag\s*\(|analytics/i);
});

test("privacy notice covers both separate editions and the data sent for AI actions", async () => {
  const html = await read("public/privacy.html");
  assert.match(html, /browser's local storage/);
  assert.match(html, /Google Gemini/);
  assert.match(html, /Anna's hosted LLM/);
  assert.match(html, /GitHub issue tracker/);
  assert.match(html, /href="\/app\/">Launch the web app/);
});

test("site map and crawler instructions use the canonical public origin", async () => {
  const html = await read("public/index.html");
  const sitemap = await read("public/sitemap.xml");
  const robots = await read("public/robots.txt");
  assert.match(html, /rel="canonical" href="https:\/\/ai-study-coach-agents\.vercel\.app\/"/);
  assert.match(sitemap, /<loc>https:\/\/ai-study-coach-agents\.vercel\.app\/<\/loc>/);
  assert.match(robots, /Sitemap: https:\/\/ai-study-coach-agents\.vercel\.app\/sitemap\.xml/);
});
