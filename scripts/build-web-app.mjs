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

// The native Anna UI source is also reused for the web edition. Rewrite
// runtime-specific status text in this generated web bundle so it accurately
// describes browser localStorage and the server-side Gemini endpoint.
const appScriptPath = path.join(publicApp, "app.js");
let appScript = await readFile(appScriptPath, "utf8");
const browserTextReplacements = [
  ["Connecting to Anna", "Preparing browser workspace"],
  ["Connected to Anna", "Browser workspace ready"],
  ["Could not connect to Anna. Open this app in Anna App Harness and retry.", "Could not connect to the browser workspace. Reload the page and retry."],
  ["Anna denied direct LLM access. Confirm ui.host_api.llm includes \"complete\" in manifest.json, then restart the app.", "The web AI service rejected the request. Reload the page and retry."],
  ["Anna's model request timed out. Try again, or shorten the study material if the error persists.", "The AI request timed out. Try again, or shorten the study material if the error persists."],
  ["Anna returned an empty response. Please try again.", "The AI service returned an empty response. Please try again."],
  ["Could not load saved profile and activity from Anna storage. This session will still work.", "Could not load saved profile and activity from this browser. This session will still work."],
  ["Profile and activity are available in this window, but Anna storage could not save them.", "Profile and activity are available in this window, but browser storage could not save them."],
  ["Your result is ready, but Anna Storage could not save your profile or activity.", "Your result is ready, but browser storage could not save your profile or activity."],
  ["Note is available in this window, but Anna Storage did not save it.", "Note is available in this window, but browser storage did not save it."],
  ["Profile updated for this session, but Anna Storage could not save it. Check your storage connection.", "Profile updated for this session, but browser storage could not save it. Check your browser storage."],
  ["History is saved in Anna storage for this app.", "History is saved in this browser."],
  ["Your study goals and activity are saved with this Anna app.", "Your study goals and activity are saved in this browser."],
  ["Working with Anna's model…", "Working with the AI service…"],
];
for (const [nativeText, browserText] of browserTextReplacements) {
  appScript = appScript.replaceAll(nativeText, browserText);
}
await writeFile(appScriptPath, appScript, "utf8");

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
