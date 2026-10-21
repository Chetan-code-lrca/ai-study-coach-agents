import { copyFile, cp, mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { build } from "esbuild";

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..");
const publicApp = path.join(root, "public", "app");
await mkdir(publicApp, { recursive: true });

const runtimeShim = path.join(root, "web-app", "anna-runtime.js");

await build({
  absWorkingDir: root,
  entryPoints: ["anna-app/src/app.js"],
  outfile: "public/app/app.js",
  bundle: true,
  minify: true,
  sourcemap: false,
  format: "esm",
  platform: "browser",
  target: ["es2022"],
  plugins: [{
    name: "browser-runtime-adapter",
    setup(builder) {
      builder.onResolve(
        { filter: /^\/static\/anna-apps\/_sdk\/latest\/index\.js$/ },
        () => ({ path: runtimeShim }),
      );
    },
  }],
});

await copyFile(
  path.join(root, "anna-app", "bundle", "index.html"),
  path.join(publicApp, "index.html"),
);
await copyFile(
  path.join(root, "anna-app", "bundle", "style.css"),
  path.join(publicApp, "style.css"),
);
await copyFile(
  path.join(root, "node_modules", "katex", "dist", "katex.min.css"),
  path.join(publicApp, "katex.min.css"),
);
await cp(
  path.join(root, "node_modules", "katex", "dist", "fonts"),
  path.join(publicApp, "fonts"),
  { recursive: true },
);
await copyFile(
  path.join(root, "node_modules", "pdfjs-dist", "build", "pdf.worker.min.mjs"),
  path.join(publicApp, "pdf.worker.min.mjs"),
);

let html = await readFile(path.join(publicApp, "index.html"), "utf8");
html = html.replace(
  "<title>AI Study Coach</title>",
  "<title>AI Study Coach — Browser App</title>",
);
html = html.replace(
  "</header>\n\n      <div class=\"intro\">",
  "</header>\n\n      <p class=\"web-edition-notice\">Browser edition: your profile, notes, plans, and quiz history are stored in this browser and do not automatically sync to Anna or other devices.</p>\n\n      <div class=\"intro\">",
);
html = html.replace(
  /<p class="profile-privacy">[\s\S]*?<\/p>/,
  '<p class="profile-privacy">This browser edition stores your study profile, saved note history, plans, and quiz activity in this browser\'s local storage. It does not ask for or store a password, and saved data does not automatically sync across browsers or devices.</p>',
);
html = html.replace(
  /<span>Text is extracted locally\.[\s\S]*?<\/span>/,
  "<span>Text is extracted locally. It is sent to the AI service only when you request an AI action; saved note history stays in this browser.</span>",
);
html = html.replace("Powered by Anna's hosted LLM", "AI requests handled securely by the web service");
if (!html.includes('id="save-note-btn"') || !html.includes('id="notes-history"')) {
  throw new Error("The source UI does not include the reviewed saved-notes workflow.");
}
await writeFile(path.join(publicApp, "index.html"), html, "utf8");

const cssPath = path.join(publicApp, "style.css");
const css = await readFile(cssPath, "utf8");
await writeFile(
  cssPath,
  css + `

/* Browser edition notice and source links */
.web-edition-notice {
  margin: 0;
  padding: 10px max(14px, calc((100% - 1020px) / 2));
  border-bottom: 1px solid var(--line);
  background: #edf4ef;
  color: var(--muted);
  font-size: 12px;
  line-height: 1.5;
}
`,
  "utf8",
);

console.log("Built the Vercel browser app in public/app, including the reviewed saved-notes workflow and local assets.");
