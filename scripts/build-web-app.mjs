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
// describes browser localStorage and browser-only offline study tools.
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
  'id="connection-label">Connecting to Anna</span>',
  'id="connection-label">Preparing browser workspace</span>',
);
html = html.replace(
  "Saved notes, study plans, and quiz results are stored in Anna Storage for this app.",
  "Saved notes, study plans, and quiz results are stored in this browser.",
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
  "Files are extracted in your browser. Their text is sent to Anna only when you request an AI action.",
  "Files are extracted and processed in this browser using built-in offline study tools. No study text is sent to an external AI provider.",
);
html = html.replace(
  /<span>Text is extracted locally\.[\s\S]*?<\/span>/,
  "<span>Text is extracted and processed locally in this browser using built-in study tools; saved note history stays in this browser.</span>",
);
html = html.replace("Powered by Anna's hosted LLM", "AI requests handled securely by the web service");

const dashboardMarkup = "<section class=\"page is-active dashboard-page\" id=\"page-dashboard\" role=\"tabpanel\">\n          <div class=\"dashboard-heading\">\n            <div>\n              <p class=\"eyebrow\">YOUR STUDY SPACE</p>\n              <h2>Your study dashboard</h2>\n              <p>Notes, study plans, practice, and progress — together in one place.</p>\n            </div>\n            <button class=\"button button-secondary dashboard-profile-link\" type=\"button\" data-open-page=\"profile\">My profile <span aria-hidden=\"true\">↗</span></button>\n          </div>\n\n          <div class=\"dashboard-action-grid\" aria-label=\"Quick actions\">\n            <button class=\"dashboard-action action-notes\" type=\"button\" data-open-page=\"learn\">\n              <span class=\"dashboard-action-icon\" aria-hidden=\"true\">▤</span>\n              <span class=\"dashboard-action-copy\"><strong>Save notes</strong><span>Upload or paste class notes and keep them organised.</span></span>\n              <span class=\"dashboard-action-arrow\" aria-hidden=\"true\">↗</span>\n            </button>\n            <button class=\"dashboard-action action-plan\" type=\"button\" data-open-page=\"plan\">\n              <span class=\"dashboard-action-icon\" aria-hidden=\"true\">▦</span>\n              <span class=\"dashboard-action-copy\"><strong>Create study plan</strong><span>Build a realistic plan around your available time.</span></span>\n              <span class=\"dashboard-action-arrow\" aria-hidden=\"true\">↗</span>\n            </button>\n            <button class=\"dashboard-action action-explain\" type=\"button\" data-open-page=\"learn\">\n              <span class=\"dashboard-action-icon\" aria-hidden=\"true\">✳</span>\n              <span class=\"dashboard-action-copy\"><strong>Explain concepts</strong><span>Review important ideas from your own material.</span></span>\n              <span class=\"dashboard-action-arrow\" aria-hidden=\"true\">↗</span>\n            </button>\n            <button class=\"dashboard-action action-quiz\" type=\"button\" data-open-page=\"quiz\">\n              <span class=\"dashboard-action-icon\" aria-hidden=\"true\">☑</span>\n              <span class=\"dashboard-action-copy\"><strong>Practice quiz</strong><span>Test your recall and review explanations.</span></span>\n              <span class=\"dashboard-action-arrow\" aria-hidden=\"true\">↗</span>\n            </button>\n          </div>\n\n          <div class=\"dashboard-columns\">\n            <section class=\"dashboard-card\" aria-labelledby=\"dashboard-notes-title\">\n              <div class=\"dashboard-card-heading\">\n                <div><p class=\"eyebrow\">YOUR MATERIAL</p><h3 id=\"dashboard-notes-title\">Recent notes</h3></div>\n                <button class=\"dashboard-text-link\" type=\"button\" data-open-page=\"learn\">View all <span aria-hidden=\"true\">→</span></button>\n              </div>\n              <div class=\"dashboard-list\" id=\"dashboard-notes\">\n                <p class=\"empty-state\">Your saved notes will appear here.</p>\n              </div>\n            </section>\n\n            <section class=\"dashboard-card\" aria-labelledby=\"dashboard-progress-title\">\n              <div class=\"dashboard-card-heading\">\n                <div><p class=\"eyebrow\">KEEP MOVING</p><h3 id=\"dashboard-progress-title\">Your progress</h3></div>\n                <button class=\"dashboard-text-link\" type=\"button\" data-open-page=\"progress\">View all <span aria-hidden=\"true\">→</span></button>\n              </div>\n              <div class=\"dashboard-metrics\">\n                <article class=\"dashboard-metric metric-green\"><strong id=\"dashboard-plans-count\">0</strong><span>Plans generated</span></article>\n                <article class=\"dashboard-metric metric-blue\"><strong id=\"dashboard-notes-count\">0</strong><span>Notes saved</span></article>\n                <article class=\"dashboard-metric metric-purple\"><strong id=\"dashboard-quizzes-count\">0</strong><span>Quizzes completed</span></article>\n                <article class=\"dashboard-metric metric-yellow\"><strong id=\"dashboard-average-score\">—</strong><span>Average score</span></article>\n              </div>\n              <div class=\"dashboard-activity-heading\"><h4>Recent activity</h4><span class=\"empty-state\">Latest updates</span></div>\n              <div class=\"dashboard-list dashboard-activity-list\" id=\"dashboard-activity\">\n                <p class=\"empty-state\">Your study activity will appear here.</p>\n              </div>\n            </section>\n          </div>\n          <p class=\"dashboard-footnote\">Your profile, notes, plans, and quiz history stay in this browser. The Vercel edition uses built-in offline study tools and does not need an API key.</p>\n        </section>";
const dashboardScript = "<script>\n(() => {\n  const storageKey = \"ai-study-coach-web:ai-study-coach:activity:v1\";\n  const $ = (id) => document.getElementById(id);\n  const formatDate = (value) => {\n    if (!value) return \"\";\n    const date = new Date(value);\n    return Number.isNaN(date.getTime()) ? \"\" : date.toLocaleDateString(undefined, { day: \"numeric\", month: \"short\" });\n  };\n  const setText = (id, value) => { const node = $(id); if (node) node.textContent = String(value); };\n  const row = ({ icon, title, detail, action, page, callback }) => {\n    const item = document.createElement(\"div\");\n    item.className = \"dashboard-list-item\";\n    const mark = document.createElement(\"span\");\n    mark.className = \"dashboard-list-icon\";\n    mark.setAttribute(\"aria-hidden\", \"true\");\n    mark.textContent = icon;\n    const copy = document.createElement(\"div\");\n    copy.className = \"dashboard-list-copy\";\n    const strong = document.createElement(\"strong\");\n    strong.textContent = title || \"Study activity\";\n    const small = document.createElement(\"span\");\n    small.textContent = detail || \"\";\n    copy.append(strong, small);\n    item.append(mark, copy);\n    if (action) {\n      const button = document.createElement(\"button\");\n      button.type = \"button\";\n      button.className = \"dashboard-list-action\";\n      button.textContent = action;\n      if (page) button.dataset.openPage = page;\n      if (callback) button.addEventListener(\"click\", callback);\n      item.append(button);\n    }\n    return item;\n  };\n  const renderList = (container, items, emptyText) => {\n    if (!container) return;\n    container.replaceChildren();\n    if (!items.length) {\n      const empty = document.createElement(\"p\");\n      empty.className = \"empty-state\";\n      empty.textContent = emptyText;\n      container.append(empty);\n      return;\n    }\n    items.forEach((item) => container.append(item));\n  };\n  function render() {\n    let saved = {};\n    try { saved = JSON.parse(localStorage.getItem(storageKey) || \"{}\") || {}; } catch { saved = {}; }\n    const plans = Array.isArray(saved.studyPlans) ? saved.studyPlans : [];\n    const notes = Array.isArray(saved.notesHistory) ? saved.notesHistory : [];\n    const quizzes = Array.isArray(saved.quizHistory) ? saved.quizHistory : [];\n    const average = quizzes.length\n      ? Math.round(quizzes.reduce((sum, item) => sum + ((Number(item.score) || 0) / Math.max(Number(item.total) || 1, 1)) * 100, 0) / quizzes.length)\n      : null;\n    setText(\"dashboard-plans-count\", plans.length);\n    setText(\"dashboard-notes-count\", notes.length);\n    setText(\"dashboard-quizzes-count\", quizzes.length);\n    setText(\"dashboard-average-score\", average === null ? \"—\" : average + \"%\");\n\n    const recentNotes = [...notes].slice(-4).reverse().map((note) => row({\n      icon: \"▤\",\n      title: note.title || \"Study notes\",\n      detail: [Array.isArray(note.sourceFiles) && note.sourceFiles.length ? note.sourceFiles.join(\", \") : \"Pasted notes\", formatDate(note.createdAt)].filter(Boolean).join(\" · \"),\n      action: \"Open\",\n      page: \"learn\"\n    }));\n    renderList($(\"dashboard-notes\"), recentNotes, \"No saved notes yet. Add or paste your first set of notes.\");\n\n    const activity = [\n      ...quizzes.map((item) => ({\n        icon: \"✓\",\n        title: item.title || item.topic || \"Practice quiz completed\",\n        detail: [formatDate(item.createdAt), item.sourceNoteTitle ? \"Based on \" + item.sourceNoteTitle : \"\"].filter(Boolean).join(\" · \"),\n        createdAt: item.createdAt,\n        score: (Number(item.score) || 0) + \"/\" + (Number(item.total) || 0),\n      })),\n      ...plans.map((item) => ({\n        icon: \"▦\",\n        title: item.subject || \"Study plan generated\",\n        detail: [formatDate(item.createdAt), item.sourceNoteTitle ? \"Notes: \" + item.sourceNoteTitle : (item.weeks ? item.weeks + \" week plan\" : \"Study plan\")].filter(Boolean).join(\" · \"),\n        createdAt: item.createdAt,\n        score: \"\",\n      })),\n      ...notes.map((item) => ({\n        icon: \"▤\",\n        title: \"Saved \" + (item.title || \"study notes\"),\n        detail: formatDate(item.createdAt),\n        createdAt: item.createdAt,\n        score: \"\",\n      }))\n    ].sort((a, b) => new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime()).slice(0, 4);\n    renderList($(\"dashboard-activity\"), activity.map((item) => {\n      const result = row({\n        icon: item.icon,\n        title: item.title,\n        detail: item.detail,\n        action: item.score,\n        page: item.score ? \"progress\" : (item.title.startsWith(\"Saved \") ? \"learn\" : \"progress\")\n      });\n      if (item.score) result.lastElementChild.classList.add(\"dashboard-score\");\n      return result;\n    }), \"Your study activity will appear here after your first plan, note, or quiz.\");\n  }\n\n  document.addEventListener(\"click\", (event) => {\n    const action = event.target.closest(\"[data-open-page]\");\n    if (!action) return;\n    const page = action.dataset.openPage;\n    const tab = document.querySelector('.tab[data-page=\"' + page + '\"]');\n    if (tab) tab.click();\n  });\n  window.addEventListener(\"study-coach:activity-updated\", render);\n  render();\n})();\n</script>";
html = html.replace(
  '<button class="tab is-active" type="button" role="tab" aria-selected="true" data-page="plan">Study plan</button>',
  '<button class="tab is-active" type="button" role="tab" aria-selected="true" data-page="dashboard">Overview</button>\n        <button class="tab" type="button" role="tab" aria-selected="false" data-page="plan">Study plan</button>',
);
html = html.replace(
  '      <nav class="tabs" role="tablist" aria-label="Study Coach sections">',
  '      <div class="workspace-layout">\n      <nav class="tabs" role="tablist" aria-label="Study Coach sections">',
);
html = html.replace(
  '      </nav>\n\n      <main>',
  '      </nav>\n\n      <div class="workspace-main">\n      <main>',
);
html = html.replace(
  '</main>\n\n      <footer class="footer">',
  '</main>\n      </div>\n      </div>\n\n      <footer class="footer">',
);
html = html.replace(
  '<section class="page is-active" id="page-plan" role="tabpanel">',
  '<section class="page" id="page-plan" role="tabpanel" hidden>',
);
html = html.replace(
  '<main>\n        <section class="page" id="page-plan" role="tabpanel" hidden>',
  '<main>\n        ' + dashboardMarkup + '\n\n        <section class="page" id="page-plan" role="tabpanel" hidden>',
);
html = html.replace(
  '<script src="app.js" type="module"></script>',
  '<script src="app.js" type="module"></script>\n    ' + dashboardScript,
);
if (!html.includes('id="page-dashboard"') || !html.includes('id="dashboard-notes"') || !html.includes('data-page="dashboard"')) {
  throw new Error("Dashboard markup could not be added to the Vercel browser edition.");
}

if (!html.includes('id="save-note-btn"') || !html.includes('id="notes-history"')) {
  throw new Error("The source UI does not include the reviewed saved-notes workflow.");
}
await writeFile(path.join(publicApp, "index.html"), html, "utf8");

const cssPath = path.join(publicApp, "style.css");
const css = await readFile(cssPath, "utf8");
await writeFile(
  cssPath,
  css + "\n/* Browser edition notice and source links */\n.web-edition-notice {\n  margin: 0;\n  padding: 10px max(14px, calc((100% - 1020px) / 2));\n  border-bottom: 1px solid var(--line);\n  background: #edf4ef;\n  color: var(--muted);\n  font-size: 12px;\n  line-height: 1.5;\n}\n\n/* Focused dashboard layout for the Vercel browser edition */\n.app-shell {\n  width: min(100%, 1500px);\n  max-width: 1500px;\n  margin: 0 auto;\n  padding: 22px clamp(18px, 3vw, 42px) 28px;\n}\n.topbar { padding-bottom: 15px; }\n.intro { padding: 20px 0 19px; }\n.intro h2 { font-size: clamp(26px, 3vw, 34px); }\n.intro > p:last-child { font-size: 14px; }\n.web-edition-notice {\n  padding: 9px 12px;\n  border: 1px solid #dce9df;\n  border-radius: 10px;\n  background: #edf5ef;\n  color: #52675c;\n  font-size: 12px;\n}\n.workspace-layout {\n  display: grid;\n  grid-template-columns: 205px minmax(0, 1fr);\n  align-items: start;\n  gap: 25px;\n}\n.workspace-main { min-width: 0; }\n.tabs {\n  position: sticky;\n  top: 16px;\n  display: flex;\n  flex-direction: column;\n  gap: 5px;\n  padding: 9px;\n  margin: 0;\n  overflow: visible;\n  border: 1px solid var(--line);\n  border-radius: 15px;\n  background: #fff;\n  box-shadow: 0 7px 22px rgba(21, 41, 31, .045);\n}\n.tab {\n  display: flex;\n  align-items: center;\n  justify-content: flex-start;\n  width: 100%;\n  min-height: 44px;\n  padding: 11px 12px;\n  border-radius: 9px;\n  color: #52675c;\n  text-align: left;\n  font-size: 13px;\n}\n.tab.is-active {\n  color: #164b37;\n  background: #e7f3ea;\n}\n.tab.is-active::after { display: none; }\n.dashboard-page { min-width: 0; }\n.dashboard-heading {\n  display: flex;\n  align-items: end;\n  justify-content: space-between;\n  gap: 18px;\n  margin: 1px 0 18px;\n}\n.dashboard-heading .eyebrow { margin-bottom: 4px; }\n.dashboard-heading h2 {\n  margin: 0 0 5px;\n  font-size: clamp(24px, 2.4vw, 30px);\n  line-height: 1.16;\n  letter-spacing: -.04em;\n}\n.dashboard-heading p:not(.eyebrow) {\n  margin: 0;\n  color: var(--muted);\n  font-size: 14px;\n}\n.dashboard-profile-link { flex: 0 0 auto; min-height: 40px; }\n.dashboard-action-grid {\n  display: grid;\n  grid-template-columns: repeat(4, minmax(0, 1fr));\n  gap: 12px;\n  margin-bottom: 17px;\n}\n.dashboard-action {\n  display: grid;\n  grid-template-columns: 42px minmax(0, 1fr);\n  grid-template-rows: auto 1fr;\n  align-items: start;\n  gap: 12px;\n  min-width: 0;\n  min-height: 158px;\n  padding: 16px 14px;\n  text-align: left;\n  border: 1px solid var(--line);\n  border-radius: 14px;\n  background: #fff;\n  color: var(--ink);\n  box-shadow: 0 5px 18px rgba(21, 41, 31, .035);\n  transition: transform .16s ease, box-shadow .16s ease, border-color .16s ease;\n}\n.dashboard-action:hover {\n  transform: translateY(-2px);\n  border-color: #b8d0c0;\n  box-shadow: 0 9px 24px rgba(21, 41, 31, .075);\n}\n.dashboard-action-icon {\n  display: grid;\n  place-items: center;\n  width: 42px;\n  height: 42px;\n  border-radius: 12px;\n  font-size: 23px;\n  font-weight: 800;\n  line-height: 1;\n}\n.action-notes .dashboard-action-icon { color: #168558; background: #dff5e8; }\n.action-plan .dashboard-action-icon { color: #286ed4; background: #e3efff; }\n.action-explain .dashboard-action-icon { color: #8648cf; background: #f0e6ff; }\n.action-quiz .dashboard-action-icon { color: #be7b00; background: #fff1c9; }\n.dashboard-action-copy { display: flex; min-width: 0; flex-direction: column; gap: 6px; }\n.dashboard-action-copy strong { font-size: 14px; line-height: 1.3; letter-spacing: -.01em; }\n.dashboard-action-copy span { color: var(--muted); font-size: 12px; font-weight: 450; line-height: 1.5; }\n.dashboard-action-arrow { grid-column: 2; align-self: end; justify-self: end; color: #789083; font-size: 17px; line-height: 1; }\n.dashboard-columns {\n  display: grid;\n  grid-template-columns: minmax(0, .95fr) minmax(0, 1.05fr);\n  gap: 14px;\n  align-items: stretch;\n}\n.dashboard-card {\n  min-width: 0;\n  padding: 18px;\n  border: 1px solid var(--line);\n  border-radius: 15px;\n  background: #fff;\n  box-shadow: 0 7px 22px rgba(21, 41, 31, .045);\n}\n.dashboard-card-heading {\n  display: flex;\n  align-items: center;\n  justify-content: space-between;\n  gap: 12px;\n  margin-bottom: 9px;\n}\n.dashboard-card-heading .eyebrow { margin-bottom: 2px; font-size: 10px; }\n.dashboard-card-heading h3 { margin: 0; font-size: 17px; letter-spacing: -.025em; }\n.dashboard-text-link {\n  flex: 0 0 auto;\n  border: 0;\n  padding: 5px 0 5px 5px;\n  color: var(--green);\n  background: transparent;\n  font-size: 12px;\n  font-weight: 750;\n}\n.dashboard-list { display: grid; min-width: 0; }\n.dashboard-list-item {\n  display: flex;\n  align-items: center;\n  gap: 10px;\n  min-width: 0;\n  padding: 12px 0;\n  border-top: 1px solid #edf1ed;\n}\n.dashboard-list-icon {\n  display: grid;\n  flex: 0 0 32px;\n  place-items: center;\n  width: 32px;\n  height: 32px;\n  border-radius: 10px;\n  color: #216d4d;\n  background: #e9f4ec;\n  font-size: 15px;\n  font-weight: 800;\n}\n.dashboard-list-copy { flex: 1 1 auto; min-width: 0; }\n.dashboard-list-copy strong {\n  display: block;\n  overflow: hidden;\n  color: var(--ink);\n  font-size: 12px;\n  font-weight: 750;\n  text-overflow: ellipsis;\n  white-space: nowrap;\n}\n.dashboard-list-copy span {\n  display: block;\n  margin-top: 3px;\n  overflow: hidden;\n  color: var(--muted);\n  font-size: 11px;\n  text-overflow: ellipsis;\n  white-space: nowrap;\n}\n.dashboard-list-action {\n  flex: 0 0 auto;\n  border: 1px solid #dce6de;\n  border-radius: 8px;\n  padding: 6px 8px;\n  color: var(--green);\n  background: #fff;\n  font-size: 11px;\n  font-weight: 750;\n}\n.dashboard-list-action:hover { background: #edf5ef; }\n.dashboard-metrics {\n  display: grid;\n  grid-template-columns: repeat(4, minmax(0, 1fr));\n  gap: 7px;\n  margin: 4px 0 17px;\n}\n.dashboard-metric {\n  min-width: 0;\n  padding: 12px 8px 10px;\n  border: 1px solid transparent;\n  border-radius: 10px;\n  text-align: center;\n}\n.dashboard-metric strong { display: block; font-size: 24px; line-height: 1.15; letter-spacing: -.035em; }\n.dashboard-metric span { display: block; margin-top: 5px; color: #52675c; font-size: 10px; line-height: 1.25; }\n.metric-green { color: #178558; background: #edf8f0; border-color: #e1f1e5; }\n.metric-blue { color: #286ed4; background: #eef5ff; border-color: #e2edfc; }\n.metric-purple { color: #8045c8; background: #f6f0ff; border-color: #eee3fc; }\n.metric-yellow { color: #a66a00; background: #fff8e5; border-color: #f8edca; }\n.dashboard-activity-heading {\n  display: flex;\n  align-items: center;\n  justify-content: space-between;\n  gap: 10px;\n  margin-bottom: 4px;\n}\n.dashboard-activity-heading h4 { margin: 0; font-size: 13px; }\n.dashboard-activity-heading .empty-state { font-size: 10px; }\n.dashboard-activity-list .dashboard-list-item { padding: 9px 0; }\n.dashboard-activity-list .dashboard-list-icon { width: 28px; height: 28px; flex-basis: 28px; border-radius: 50%; color: #197c52; background: #e5f5eb; }\n.dashboard-footnote {\n  margin: 14px 2px 0;\n  color: var(--muted);\n  font-size: 11px;\n  line-height: 1.5;\n}\n.dashboard-page .empty-state { padding: 12px 0; }\n@media (max-width: 1120px) {\n  .workspace-layout { grid-template-columns: 180px minmax(0, 1fr); gap: 17px; }\n  .dashboard-action-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }\n  .dashboard-action { min-height: 128px; }\n  .dashboard-columns { grid-template-columns: minmax(0, 1fr); }\n}\n@media (max-width: 760px) {\n  .app-shell { padding: 14px 14px 22px; }\n  .workspace-layout { grid-template-columns: minmax(0, 1fr); gap: 16px; }\n  .tabs {\n    position: static;\n    display: grid;\n    grid-template-columns: repeat(3, minmax(0, 1fr));\n    gap: 4px;\n    padding: 6px;\n  }\n  .tab { justify-content: center; min-height: 40px; padding: 9px 6px; text-align: center; font-size: 12px; }\n  .dashboard-heading { align-items: start; }\n  .dashboard-heading h2 { font-size: 25px; }\n}\n@media (max-width: 480px) {\n  .dashboard-action-grid { grid-template-columns: minmax(0, 1fr); }\n  .dashboard-action { min-height: auto; grid-template-rows: auto; grid-template-columns: 42px minmax(0, 1fr) 15px; align-items: center; padding: 13px; }\n  .dashboard-action-arrow { grid-column: 3; grid-row: 1; }\n  .dashboard-metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }\n  .dashboard-card { padding: 14px; }\n  .dashboard-heading { flex-direction: column; }\n  .dashboard-profile-link { align-self: flex-start; }\n}\n@media (prefers-reduced-motion: reduce) {\n  .dashboard-action { transition: none; }\n}\n\n",
  "utf8",
);

console.log("Built the Vercel browser app in public/app, including the reviewed saved-notes workflow and local assets.");
