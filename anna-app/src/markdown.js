import katex from "katex";

/**
 * Render the Markdown subset used by model answers, including TeX math.
 * Ordinary text is HTML-escaped before markup is introduced. Math passes
 * through KaTeX with trust disabled and error recovery enabled.
 */
function escapeHtml(value) {
  return String(value).replace(/[&<>"]/g, (character) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
  })[character]);
}

function protectMathExpressions(text, expressions) {
  const patterns = [
    { regex: /\$\$([\s\S]+?)\$\$/g, display: true },
    { regex: /\\\[([\s\S]+?)\\\]/g, display: true },
    { regex: /\\\(([\s\S]+?)\\\)/g, display: false },
    { regex: /\$([^\n$]+?)\$/g, display: false },
  ];
  let protectedText = text;
  for (const { regex, display } of patterns) {
    protectedText = protectedText.replace(regex, (_match, expression) => {
      const index = expressions.length;
      expressions.push({ expression: expression.trim(), display });
      return `KATEXMATH${index}TOKEN`;
    });
  }
  return protectedText;
}

function protectMathOutsideCode(markdown) {
  const expressions = [];
  const output = [];
  let normalLines = [];
  let inCode = false;

  const flushNormalText = () => {
    if (!normalLines.length) return;
    output.push(protectMathExpressions(normalLines.join("\n"), expressions));
    normalLines = [];
  };

  for (const line of String(markdown).replace(/\r\n?/g, "\n").split("\n")) {
    if (line.trim().startsWith("```")) {
      flushNormalText();
      output.push(line);
      inCode = !inCode;
    } else if (inCode) {
      output.push(line);
    } else {
      normalLines.push(line);
    }
  }
  flushNormalText();
  return { text: output.join("\n"), expressions };
}

function renderMath(expression, display) {
  const rendered = katex.renderToString(expression, {
    displayMode: display,
    throwOnError: false,
    trust: false,
  });
  return display
    ? `<div class="math-display">${rendered}</div>`
    : `<span class="math-inline">${rendered}</span>`;
}

function restoreMath(html, expressions) {
  // A block equation by itself should not be nested inside a paragraph.
  html = html.replace(/<p>\s*KATEXMATH(\d+)TOKEN\s*<\/p>/g, (paragraph, index) => {
    const item = expressions[Number(index)];
    if (!item) return paragraph;
    return item.display
      ? renderMath(item.expression, true)
      : `<p>${renderMath(item.expression, false)}</p>`;
  });
  return html.replace(/KATEXMATH(\d+)TOKEN/g, (token, index) => {
    const item = expressions[Number(index)];
    return item ? renderMath(item.expression, item.display) : token;
  });
}

function inlineMarkdown(escaped) {
  return escaped
    .replace(/`([^`]+)`/g, "<code>$1</code>")
    .replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>")
    .replace(/\*([^*]+)\*/g, "<em>$1</em>");
}

export function renderMarkdown(markdown) {
  const protectedContent = protectMathOutsideCode(markdown);
  const lines = escapeHtml(protectedContent.text).split("\n");
  const output = [];
  let paragraph = [];
  let listType = null;
  let inCode = false;
  let codeLines = [];

  const flushParagraph = () => {
    if (!paragraph.length) return;
    output.push(`<p>${paragraph.map(inlineMarkdown).join(" ")}</p>`);
    paragraph = [];
  };
  const closeList = () => {
    if (listType) output.push(`</${listType}>`);
    listType = null;
  };
  const openList = (type) => {
    if (listType === type) return;
    closeList();
    output.push(`<${type}>`);
    listType = type;
  };

  for (const line of lines) {
    if (line.trim().startsWith("```")) {
      flushParagraph();
      closeList();
      if (inCode) {
        output.push(`<pre><code>${codeLines.join("\n")}</code></pre>`);
        codeLines = [];
        inCode = false;
      } else {
        inCode = true;
      }
      continue;
    }
    if (inCode) {
      codeLines.push(line);
      continue;
    }

    if (!line.trim()) {
      flushParagraph();
      closeList();
      continue;
    }

    const heading = line.match(/^(#{1,6})\s+(.+)$/);
    if (heading) {
      flushParagraph();
      closeList();
      const level = heading[1].length;
      output.push(`<h${level}>${inlineMarkdown(heading[2])}</h${level}>`);
      continue;
    }

    if (/^\s*(---+|___+|\*\*\*+)\s*$/.test(line)) {
      flushParagraph();
      closeList();
      output.push("<hr>");
      continue;
    }

    const unordered = line.match(/^\s*[-*+]\s+(.+)$/);
    const ordered = line.match(/^\s*\d+[.)]\s+(.+)$/);
    if (unordered || ordered) {
      flushParagraph();
      openList(unordered ? "ul" : "ol");
      output.push(`<li>${inlineMarkdown((unordered || ordered)[1])}</li>`);
      continue;
    }

    const quote = line.match(/^\s*&gt;\s?(.*)$/);
    if (quote) {
      flushParagraph();
      closeList();
      output.push(`<blockquote><p>${inlineMarkdown(quote[1])}</p></blockquote>`);
      continue;
    }

    closeList();
    paragraph.push(line.trim());
  }

  flushParagraph();
  closeList();
  if (inCode) output.push(`<pre><code>${codeLines.join("\n")}</code></pre>`);
  return restoreMath(output.join("\n"), protectedContent.expressions);
}
