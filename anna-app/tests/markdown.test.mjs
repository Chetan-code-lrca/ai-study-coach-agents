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

test("renders inline LaTeX in formulas and statistics", () => {
  const html = renderMarkdown("Mean ($\\\\bar{x}$): $\\\\frac{\\\\sum x}{n}$");
  assert.match(html, /class="math-inline"/);
  assert.match(html, /class="katex"/);
  assert.match(html, /class="mord mathnormal"/);
  assert.match(html, /<span class="katex-mathml">/);
  assert.doesNotMatch(html, /\\$\\\\bar\{x\}\\$/);
});

test("renders standalone display equations as centered math blocks", () => {
  const html = renderMarkdown("Regression formula:\\n\\n$$\\\\hat{y} = b_0 + b_1x$$");
  assert.match(html, /<div class="math-display">/);
  assert.match(html, /class="katex-display"/);
  assert.doesNotMatch(html, /<p><div class="math-display">/);
});

test("supports LaTeX bracket and parenthesis delimiters", () => {
  const html = renderMarkdown("Inline \\\\(x^2 + y^2\\\\) and display:\\n\\n\\\\[\\\\sigma^2 = \\\\frac{\\\\sum (x-\\\\bar{x})^2}{n}\\\\]");
  assert.equal((html.match(/class="katex"/g) || []).length, 2);
  assert.match(html, /math-display/);
});

test("leaves formulas inside fenced code blocks as code", () => {
  const html = renderMarkdown("Example code:\\n\\n```text\\n$x$\\n```");
  assert.match(html, /<pre><code>\$x\$<\\/code><\\/pre>/);
  assert.doesNotMatch(html, /class="katex"/);
});

test("shows invalid LaTeX as text without breaking the full answer", () => {
  const html = renderMarkdown("Formula: $\\\\thisIsNotARealCommand{x}$\\n\\nThe rest of the answer remains available.");
  assert.match(html, /katex-error/);
  assert.match(html, /The rest of the answer remains available/);
});
