import assert from "node:assert/strict";
import test from "node:test";
import { renderMarkdown } from "../src/markdown.js";

test("renders common study-answer Markdown as headings, paragraphs, and lists", () => {
  const html = renderMarkdown("# Overview\n\nA **semaphore** controls access.\n\n- Wait operation\n- Signal operation\n\nUse code wait().");
  assert.match(html, /<h1>Overview<\/h1>/);
  assert.match(html, /<strong>semaphore<\/strong>/);
  assert.match(html, /<ul>/);
  assert.match(html, /<li>Wait operation<\/li>/);
  assert.match(html, /controls access/);
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
  const formula = "Mean ($\\bar{x}$): $\\frac{\\sum x}{n}$";
  const html = renderMarkdown(formula);
  assert.match(html, /class="math-inline"/);
  assert.match(html, /class="katex"/);
  assert.match(html, /class="katex-mathml"/);
  assert.doesNotMatch(html, /\\bar\{x\}/);
});

test("renders standalone display equations as centered math blocks", () => {
  const formula = "$$\\hat{y} = b_0 + b_1x$$";
  const html = renderMarkdown("Regression formula:\n\n" + formula);
  assert.match(html, /<div class="math-display">/);
  assert.match(html, /class="katex-display"/);
  assert.doesNotMatch(html, /<p><div class="math-display">/);
});

test("supports LaTeX bracket and parenthesis delimiters", () => {
  const inline = "\\(x^2 + y^2\\)";
  const display = "\\[\\sigma^2 = \\frac{\\sum (x-\\bar{x})^2}{n}\\]";
  const html = renderMarkdown("Inline " + inline + " and display:\n\n" + display);
  assert.equal((html.match(/class="katex"/g) || []).length, 2);
  assert.match(html, /math-display/);
});

test("leaves formulas inside fenced code blocks as code", () => {
  const fence = String.fromCharCode(96).repeat(3);
  const html = renderMarkdown("Example code:\n\n" + fence + "text\n$x$\n" + fence);
  assert.match(html, /<pre><code>\$x\$<\/code><\/pre>/);
  assert.doesNotMatch(html, /class="katex"/);
});

test("shows invalid LaTeX without breaking the rest of the answer", () => {
  const broken = "$\\thisIsNotARealCommand{x}$";
  const html = renderMarkdown("Formula: " + broken + "\n\nThe rest of the answer remains available.");
  assert.match(html, /mathcolor="#cc0000"/);
  assert.match(html, /The rest of the answer remains available/);
});
