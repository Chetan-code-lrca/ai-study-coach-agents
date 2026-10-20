import assert from "node:assert/strict";
import test from "node:test";
import { renderMarkdown } from "../src/markdown.js";

test("renders common study-answer Markdown as headings, paragraphs, and lists", () => {
  const html = renderMarkdown("# Overview\n\nA **semaphore** controls access.\n\n- Wait operation\n- Signal operation\n\nUse `wait()`.");
  assert.match(html, /<h1>Overview<\/h1>/);
  assert.match(html, /<strong>semaphore<\/strong>/);
  assert.match(html, /<ul>/);
  assert.match(html, /<li>Wait operation<\/li>/);
  assert.match(html, /<code>wait\(\)<\/code>/);
});

test("escapes HTML in model output before adding presentation markup", () => {
  const html = renderMarkdown('## Result\n\n<script>alert("x")</script> **safe text**');
  assert.match(html, /&lt;script&gt;/);
  assert.doesNotMatch(html, /<script>/);
  assert.match(html, /<strong>safe text<\/strong>/);
});

test("preserves Unicode extracted from local study files", () => {
  const html = renderMarkdown("Direction: ↓ then ↑; implication →; café.");
  assert.match(html, /↓ then ↑/);
  assert.match(html, /implication →/);
  assert.match(html, /café/);
});
