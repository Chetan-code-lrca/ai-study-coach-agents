import { AnnaAppRuntime } from "/static/anna-apps/_sdk/latest/index.js";
import * as pdfjsLib from "pdfjs-dist/build/pdf.mjs";
import mammoth from "mammoth";
import { buildStudyRequest } from "./study-prompts.js";
import { renderMarkdown } from "./markdown.js";

const STORAGE_KEY = "ai-study-coach:activity:v1";

const $ = (id) => document.getElementById(id);
const state = {
  studyPlans: [],
  quizHistory: [],
  currentQuiz: null,
  answers: {},
  quizSubmitted: false,
  attachedFiles: [],
};
let anna = null;

function setStatus(element, message, kind = "") {
  if (!element) return;
  element.textContent = message;
  element.classList.remove("is-error", "is-success");
  if (kind) element.classList.add(kind === "error" ? "is-error" : "is-success");
}

function showToast(message) {
  const toast = $("app-status");
  if (!toast) return;
  toast.textContent = message;
  toast.classList.add("is-visible");
  window.setTimeout(() => toast.classList.remove("is-visible"), 3200);
}

function getErrorMessage(error) {
  const message = error?.message || String(error || "Unknown error");
  if (/manifest does not grant.*llm\.complete/i.test(message)) {
    return "Anna denied direct LLM access. Confirm ui.host_api.llm includes \"complete\" in manifest.json, then restart the app.";
  }
  if (/timeout|timed out/i.test(message)) {
    return "Anna's model request timed out. Try again, or shorten the study material if the error persists.";
  }
  if (/context length|too many tokens|prompt.{0,20}too long/i.test(message)) {
    return "This request is too large for the selected model. Clear some material or summarize a shorter section first.";
  }
  return message;
}

function extractCompletionText(reply) {
  const content = reply?.content ?? reply?.message?.content ?? reply?.data?.content;
  if (typeof content === "string" && content.trim()) return content.trim();
  if (content && !Array.isArray(content) && content.type === "text" &&
      typeof content.text === "string" && content.text.trim()) {
    return content.text.trim();
  }
  if (Array.isArray(content)) {
    const combined = content
      .filter((block) => block && block.type === "text" && typeof block.text === "string")
      .map((block) => block.text)
      .join("\\n")
      .trim();
    if (combined) return combined;
  }
  if (typeof reply?.text === "string" && reply.text.trim()) return reply.text.trim();
  throw new Error("Anna returned an empty response. Please try again.");
}

async function completeStudyAction(action, payload) {
  if (!anna) throw new Error("Anna runtime is not connected. Open this app inside the Anna App Harness and retry.");
  const request = buildStudyRequest(action, payload);
  // Use the documented frontend-to-host LLM API directly. This keeps source
  // text (including Unicode extracted from PDFs) out of a Windows Python
  // Executa subprocess and its locale-dependent stdio encoding.
  const reply = await anna.llm.complete({
    messages: [
      { role: "user", content: { type: "text", text: request.prompt } },
    ],
    systemPrompt: request.systemPrompt,
    maxTokens: request.maxTokens,
    temperature: 0.3,
  });
  return {
    action,
    text: extractCompletionText(reply),
    model: reply?.model,
    usage: reply?.usage,
  };
}

async function loadActivity() {
  try {
    const stored = await anna.storage.get({ key: STORAGE_KEY });
    let value = stored && typeof stored === "object" && "value" in stored ? stored.value : stored;
    if (typeof value === "string") value = JSON.parse(value);
    if (value && typeof value === "object") {
      if (Array.isArray(value.studyPlans)) state.studyPlans = value.studyPlans;
      if (Array.isArray(value.quizHistory)) state.quizHistory = value.quizHistory;
    }
  } catch (error) {
    setStatus($("progress-status"), "Could not load saved activity from Anna storage. This session will still work.");
  }
  renderProgress();
}

async function saveActivity() {
  try {
    await anna.storage.set({
      key: STORAGE_KEY,
      value: {
        studyPlans: state.studyPlans.slice(-50),
        quizHistory: state.quizHistory.slice(-100),
      },
    });
    return true;
  } catch (error) {
    setStatus($("progress-status"), "Activity is available in this window, but Anna storage could not save it.");
    showToast("Your result was created, but activity could not be saved.");
    return false;
  }
}

async function runAction(button, statusElement, action, payload) {
  if (button.disabled) return null;
  const oldLabel = button.textContent;
  button.disabled = true;
  button.setAttribute("aria-busy", "true");
  setStatus(statusElement, "Working with Anna's model…");
  try {
    const data = await completeStudyAction(action, payload);
    setStatus(statusElement, "Done.", "success");
    return data;
  } catch (error) {
    setStatus(statusElement, getErrorMessage(error), "error");
    return null;
  } finally {
    button.disabled = false;
    button.removeAttribute("aria-busy");
    button.textContent = oldLabel;
  }
}

function showResult(card, textElement, titleElement, title, text) {
  if (titleElement) titleElement.textContent = title;
  textElement.innerHTML = renderMarkdown(text);
  card.hidden = false;
}

function renderHistoryList(container, items, kind) {
  container.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = kind === "plan" ? "No study plans yet." : "No quiz attempts yet.";
    container.append(empty);
    return;
  }

  for (const item of [...items].slice(-8).reverse()) {
    const row = document.createElement("div");
    row.className = "history-item";
    const copy = document.createElement("div");
    const title = document.createElement("strong");
    const detail = document.createElement("span");
    const score = document.createElement("div");
    if (kind === "plan") {
      title.textContent = item.subject || "Study plan";
      detail.textContent = [item.level, item.weeks ? `${item.weeks} week(s)` : "", formatDate(item.createdAt)].filter(Boolean).join(" · ");
      score.textContent = "Plan";
    } else {
      title.textContent = item.title || item.topic || "Practice quiz";
      detail.textContent = formatDate(item.createdAt);
      score.className = "history-score";
      score.textContent = `${item.score}/${item.total}`;
    }
    copy.append(title, detail);
    row.append(copy, score);
    container.append(row);
  }
}

function formatDate(value) {
  if (!value) return "";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "";
  return date.toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

function renderProgress() {
  $("plans-count").textContent = String(state.studyPlans.length);
  $("quizzes-count").textContent = String(state.quizHistory.length);
  if (state.quizHistory.length) {
    const average = state.quizHistory.reduce((sum, item) => sum + (item.score / Math.max(item.total, 1)) * 100, 0) / state.quizHistory.length;
    $("average-score").textContent = `${Math.round(average)}%`;
  } else {
    $("average-score").textContent = "—";
  }
  renderHistoryList($("plan-history"), state.studyPlans, "plan");
  renderHistoryList($("quiz-history"), state.quizHistory, "quiz");
}

function addStorageHistoryNotice() {
  const status = $("progress-status");
  if (status && !status.textContent) {
    setStatus(status, "History is saved in Anna storage for this app.");
  }
}

function parseQuiz(raw) {
  let cleaned = raw.trim();
  if (cleaned.startsWith("```")) {
    cleaned = cleaned.replace(/^```(?:json)?\s*/i, "").replace(/\s*```$/, "");
  }
  const quiz = JSON.parse(cleaned);
  if (!quiz || typeof quiz !== "object" || !Array.isArray(quiz.questions) || quiz.questions.length < 3) {
    throw new Error("Anna returned a quiz in an unexpected format. Try generating it again.");
  }
  quiz.title = typeof quiz.title === "string" && quiz.title.trim() ? quiz.title.trim() : "Practice quiz";
  quiz.questions = quiz.questions.map((question, index) => {
    if (!question || typeof question.question !== "string" || !Array.isArray(question.options) || question.options.length !== 4 ||
        !question.options.every((option) => typeof option === "string") ||
        !Number.isInteger(question.correct_index) || question.correct_index < 0 || question.correct_index > 3) {
      throw new Error(`Question ${index + 1} was incomplete. Try generating the quiz again.`);
    }
    return {
      question: question.question,
      options: question.options,
      correct_index: question.correct_index,
      explanation: typeof question.explanation === "string" ? question.explanation : "",
    };
  });
  return quiz;
}

function renderQuiz() {
  const root = $("quiz-result");
  root.replaceChildren();
  if (!state.currentQuiz) {
    root.hidden = true;
    return;
  }
  root.hidden = false;

  const heading = document.createElement("div");
  heading.className = "quiz-card";
  const title = document.createElement("h3");
  title.className = "quiz-title";
  title.textContent = state.currentQuiz.title;
  const note = document.createElement("p");
  note.className = "empty-state";
  note.textContent = state.quizSubmitted ? "Review each answer and the explanation." : "Choose one answer for each question, then submit to see your score.";
  heading.append(title, note);
  root.append(heading);

  state.currentQuiz.questions.forEach((question, index) => {
    const card = document.createElement("article");
    card.className = "quiz-card";
    const prompt = document.createElement("p");
    prompt.className = "quiz-question";
    prompt.textContent = `${index + 1}. ${question.question}`;
    card.append(prompt);
    question.options.forEach((option, optionIndex) => {
      const label = document.createElement("label");
      label.className = "quiz-option";
      if (state.quizSubmitted && optionIndex === question.correct_index) {
        label.classList.add("quiz-option-correct");
      } else if (state.quizSubmitted && state.answers[index] === optionIndex) {
        label.classList.add("quiz-option-incorrect");
      }
      const input = document.createElement("input");
      input.type = "radio";
      input.name = `quiz-answer-${index}`;
      input.value = String(optionIndex);
      input.checked = state.answers[index] === optionIndex;
      input.disabled = state.quizSubmitted;
      input.addEventListener("change", () => { state.answers[index] = optionIndex; });
      const text = document.createElement("span");
      text.textContent = option;
      label.append(input, text);
      card.append(label);
    });
    if (state.quizSubmitted) {
      const explanation = document.createElement("p");
      explanation.className = "quiz-explanation";
      explanation.textContent = `Correct answer: ${question.options[question.correct_index]}. ${question.explanation}`;
      card.append(explanation);
    }
    root.append(card);
  });

  if (state.quizSubmitted) {
    const score = state.quizHistory[ state.quizHistory.length - 1 ];
    const feedback = document.createElement("div");
    feedback.className = "quiz-feedback";
    feedback.textContent = score ? `Your score: ${score.score}/${score.total} (${Math.round(score.score / score.total * 100)}%). Review the explanations above and retry later for active recall.` : "Quiz submitted.";
    root.append(feedback);
  } else {
    const submit = document.createElement("button");
    submit.type = "button";
    submit.className = "button button-primary";
    submit.textContent = "Submit answers";
    submit.addEventListener("click", submitQuiz);
    root.append(submit);
  }
}

async function submitQuiz() {
  if (!state.currentQuiz || state.quizSubmitted) return;
  const questions = state.currentQuiz.questions;
  const score = questions.reduce((total, question, index) => total + Number(state.answers[index] === question.correct_index), 0);
  state.quizSubmitted = true;
  state.quizHistory.push({
    title: state.currentQuiz.title,
    topic: $("quiz-topic").value.trim(),
    score,
    total: questions.length,
    createdAt: new Date().toISOString(),
  });
  renderQuiz();
  renderProgress();
  setStatus($("quiz-status"), "Quiz submitted. Your score has been recorded.", "success");
  await saveActivity();
  addStorageHistoryNotice();
}

function setActivePage(name) {
  document.querySelectorAll(".tab").forEach((tab) => {
    const selected = tab.dataset.page === name;
    tab.classList.toggle("is-active", selected);
    tab.setAttribute("aria-selected", String(selected));
  });
  document.querySelectorAll(".page").forEach((page) => {
    const active = page.id === `page-${name}`;
    page.classList.toggle("is-active", active);
    page.hidden = !active;
  });
  if (name === "progress") renderProgress();
}

document.querySelectorAll(".tab").forEach((tab) => {
  tab.addEventListener("click", () => setActivePage(tab.dataset.page));
});

$("plan-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const button = $("plan-submit");
  const data = await runAction(button, $("plan-status"), "generate_study_plan", {
    subject: $("plan-subject").value.trim(),
    level: $("plan-level").value,
    weeks: Number($("plan-weeks").value),
    hours_per_day: Number($("plan-hours").value),
    goals: $("plan-goals").value.trim(),
  });
  if (!data) return;
  showResult($("plan-result"), $("plan-result-text"), null, "YOUR PLAN", data.text);
  state.studyPlans.push({
    subject: $("plan-subject").value.trim(),
    level: $("plan-level").value,
    weeks: Number($("plan-weeks").value),
    createdAt: new Date().toISOString(),
  });
  renderProgress();
  await saveActivity();
  addStorageHistoryNotice();
});

const MAX_FILE_BYTES = 10 * 1024 * 1024;
const MAX_MATERIAL_CHARS = 30000;
const SUPPORTED_FILE_TYPES = new Set(["pdf", "docx", "txt", "md", "csv", "json"]);

function updateMaterialCount() {
  $("material-count").textContent = `${$("material-text").value.length.toLocaleString()} / ${MAX_MATERIAL_CHARS.toLocaleString()} characters`;
}

function fileExtension(fileName) {
  const dot = String(fileName || "").lastIndexOf(".");
  return dot >= 0 ? fileName.slice(dot + 1).toLowerCase() : "";
}

function formatFileSize(size) {
  if (size < 1024) return `${size} B`;
  if (size < 1024 * 1024) return `${(size / 1024).toFixed(1)} KB`;
  return `${(size / (1024 * 1024)).toFixed(1)} MB`;
}

async function getPdfJs() {
  pdfjsLib.GlobalWorkerOptions.workerSrc = new URL("./pdf.worker.min.mjs", import.meta.url).toString();
  return pdfjsLib;
}

async function getMammoth() {
  return mammoth;
}

async function extractPdfText(file) {
  const pdfjs = await getPdfJs();
  const bytes = new Uint8Array(await file.arrayBuffer());
  const loadingTask = pdfjs.getDocument({ data: bytes, isEvalSupported: false });
  try {
    const pdf = await loadingTask.promise;
    const pages = [];
    let characterCount = 0;
    for (let pageNumber = 1; pageNumber <= pdf.numPages; pageNumber += 1) {
      const page = await pdf.getPage(pageNumber);
      const content = await page.getTextContent();
      const pageText = content.items
        .filter((item) => item && typeof item.str === "string")
        .map((item) => item.str)
        .join(" ")
        .trim();
      if (pageText) pages.push(pageText);
      characterCount += pageText.length;
      if (characterCount >= MAX_MATERIAL_CHARS) break;
    }
    return { text: pages.join("\n\n"), detail: `${pdf.numPages} page(s)` };
  } finally {
    // PDF.js exposes destroy() on the loading task, not the document proxy.
    await loadingTask.destroy();
  }
}

async function extractFileText(file) {
  const extension = fileExtension(file.name);
  if (!SUPPORTED_FILE_TYPES.has(extension)) {
    throw new Error(`Unsupported file type: .${extension || "(none)"}. Use PDF, DOCX, TXT, MD, CSV, or JSON.`);
  }
  if (file.size > MAX_FILE_BYTES) {
    throw new Error(`${file.name} exceeds the 10 MB per-file limit.`);
  }
  if (!file.size) throw new Error(`${file.name} is empty.`);

  if (extension === "pdf") return extractPdfText(file);
  if (extension === "docx") {
    const mammoth = await getMammoth();
    const result = await mammoth.extractRawText({ arrayBuffer: await file.arrayBuffer() });
    return { text: result.value || "", detail: "Word document" };
  }
  const text = (await file.text()).replace(/^\uFEFF/, "");
  return { text, detail: extension.toUpperCase() };
}

function renderAttachedFiles() {
  const container = $("attached-files");
  const list = $("attached-files-list");
  list.replaceChildren();
  container.hidden = state.attachedFiles.length === 0;
  $("attached-files-count").textContent = `${state.attachedFiles.length} file(s) loaded`;
  for (const file of state.attachedFiles) {
    const item = document.createElement("li");
    item.className = "attached-file-item";
    const icon = document.createElement("span");
    icon.className = "attached-file-icon";
    icon.setAttribute("aria-hidden", "true");
    icon.textContent = file.extension === "pdf" ? "PDF" : file.extension.toUpperCase();
    const details = document.createElement("span");
    details.className = "attached-file-details";
    const name = document.createElement("span");
    name.className = "attached-file-name";
    name.textContent = file.name;
    const meta = document.createElement("span");
    meta.className = "attached-file-meta";
    meta.textContent = `${formatFileSize(file.size)} · ${file.characters.toLocaleString()} characters extracted${file.truncated ? " · text truncated to fit the study-material limit" : ""}`;
    details.append(name, meta);
    item.append(icon, details);
    list.append(item);
  }
}

async function handleSelectedFiles(fileList) {
  const files = Array.from(fileList || []);
  if (!files.length) return;
  const button = $("choose-files-btn");
  button.disabled = true;
  let loaded = 0;
  let truncatedAny = false;
  const errors = [];
  try {
    for (const file of files) {
      const currentLength = $("material-text").value.length;
      const freeCharacters = MAX_MATERIAL_CHARS - currentLength;
      if (freeCharacters < 64) {
        errors.push("The 30,000-character study-material limit has been reached. Clear or shorten the material before adding more.");
        break;
      }
      try {
        const extracted = await extractFileText(file);
        const text = String(extracted.text || "").trim();
        if (!text) {
          throw new Error(fileExtension(file.name) === "pdf"
            ? "No selectable text was found. Scanned/image-only PDFs need OCR, which is not included yet."
            : "No readable text was found.");
        }
        const separator = `\n\n--- Source file: ${file.name} ---\n`;
        const availableForText = Math.max(0, freeCharacters - separator.length);
        if (!availableForText) {
          errors.push(`Not enough space to add ${file.name}. Clear or shorten the material first.`);
          break;
        }
        const addedText = text.slice(0, availableForText);
        const truncated = addedText.length < text.length;
        $("material-text").value += separator + addedText;
        state.attachedFiles.push({
          name: file.name,
          size: file.size,
          extension: fileExtension(file.name),
          characters: addedText.length,
          truncated,
        });
        loaded += 1;
        truncatedAny = truncatedAny || truncated;
        updateMaterialCount();
        renderAttachedFiles();
        if (truncated) {
          errors.push(`${file.name} was shortened to fit the 30,000-character limit. Remove or shorten earlier material to add the rest.`);
          break;
        }
      } catch (error) {
        errors.push(`${file.name}: ${error?.message || error}`);
      }
    }

    if (loaded > 0) {
      const summary = `Loaded ${loaded} file(s). Review the extracted text below before using it.`;
      const detail = errors.length ? ` ${errors.join(" ")}` : "";
      setStatus($("file-status"), summary + detail, errors.length ? "error" : "success");
      $("material-text").focus();
    } else if (errors.length) {
      setStatus($("file-status"), errors.join(" "), "error");
    }
    if (truncatedAny && !errors.length) {
      setStatus($("file-status"), "Some text was shortened to fit the 30,000-character limit.", "error");
    }
  } finally {
    button.disabled = false;
    $("file-input").value = "";
  }
}

$("choose-files-btn").addEventListener("click", () => $("file-input").click());
$("file-input").addEventListener("change", (event) => handleSelectedFiles(event.target.files));

const fileDropZone = $("file-drop-zone");
fileDropZone.addEventListener("dragover", (event) => {
  event.preventDefault();
  fileDropZone.classList.add("is-dragover");
});
fileDropZone.addEventListener("dragenter", (event) => {
  event.preventDefault();
  fileDropZone.classList.add("is-dragover");
});
fileDropZone.addEventListener("dragleave", (event) => {
  if (!fileDropZone.contains(event.relatedTarget)) fileDropZone.classList.remove("is-dragover");
});
fileDropZone.addEventListener("drop", (event) => {
  event.preventDefault();
  fileDropZone.classList.remove("is-dragover");
  handleSelectedFiles(event.dataTransfer?.files);
});

$("clear-material-btn").addEventListener("click", () => {
  $("material-text").value = "";
  state.attachedFiles = [];
  renderAttachedFiles();
  updateMaterialCount();
  setStatus($("file-status"), "Study material cleared.");
  setStatus($("learn-status"), "");
});

$("use-for-quiz-btn").addEventListener("click", () => {
  const material = $("material-text").value.trim();
  if (!material) {
    setStatus($("file-status"), "Add or paste study material first.", "error");
    return;
  }
  $("quiz-source").value = material;
  setActivePage("quiz");
  setStatus($("quiz-status"), "Study material copied into the quiz source field. Enter a topic and generate your quiz.", "success");
});

$("material-text").addEventListener("input", updateMaterialCount);
updateMaterialCount();

async function runMaterialAction(buttonId, action, title) {
  const material = $("material-text").value.trim();
  if (!material) {
    setStatus($("learn-status"), "Paste or type your study material first.", "error");
    $("material-text").focus();
    return;
  }
  const payload = { material };
  if (action === "answer_question") {
    payload.question = $("question-text").value.trim();
    if (!payload.question) {
      setStatus($("learn-status"), "Enter a question first.", "error");
      $("question-text").focus();
      return;
    }
  }
  const data = await runAction($(buttonId), $("learn-status"), action, payload);
  if (data) showResult($("learn-result"), $("learn-result-text"), $("learn-result-title"), title, data.text);
}

$("summarize-btn").addEventListener("click", () => runMaterialAction("summarize-btn", "summarize_material", "SUMMARY"));
$("explain-btn").addEventListener("click", () => runMaterialAction("explain-btn", "explain_concepts", "KEY CONCEPTS"));
$("answer-btn").addEventListener("click", () => runMaterialAction("answer-btn", "answer_question", "ANSWER FROM YOUR NOTES"));

$("quiz-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const topic = $("quiz-topic").value.trim();
  if (!topic) {
    setStatus($("quiz-status"), "Enter a quiz topic first.", "error");
    $("quiz-topic").focus();
    return;
  }
  const data = await runAction($("quiz-submit"), $("quiz-status"), "generate_quiz", {
    topic,
    difficulty: $("quiz-difficulty").value,
    count: Number($("quiz-count").value),
    source_material: $("quiz-source").value.trim(),
  });
  if (!data) return;
  try {
    const quiz = parseQuiz(data.text);
    if (quiz.questions.length !== Number($("quiz-count").value)) {
      throw new Error(`Expected ${$("quiz-count").value} questions, but received ${quiz.questions.length}. Try generating it again.`);
    }
    state.currentQuiz = quiz;
    state.answers = {};
    state.quizSubmitted = false;
    renderQuiz();
    setStatus($("quiz-status"), "Quiz ready. Choose your answers below.", "success");
    $("quiz-result").scrollIntoView({ behavior: "smooth", block: "start" });
  } catch (error) {
    setStatus($("quiz-status"), getErrorMessage(error), "error");
  }
});

document.querySelectorAll("[data-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    const target = $(button.dataset.copy);
    const text = target?.querySelector(".result-text")?.innerText || target?.innerText || target?.textContent || "";
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      showToast("Copied to clipboard.");
    } catch (error) {
      showToast("Clipboard access is unavailable in this window.");
    }
  });
});

async function bootstrap() {
  try {
    anna = await AnnaAppRuntime.connect();
    await anna.window.set_title({ title: "AI Study Coach" });
    $("connection-label").textContent = "Connected to Anna";
    document.querySelector(".runtime-pill").classList.add("is-connected");
    await loadActivity();
    addStorageHistoryNotice();
  } catch (error) {
    $("connection-label").textContent = "Not connected";
    setStatus($("plan-status"), "Could not connect to Anna. Open this app in Anna App Harness and retry.", "error");
    setStatus($("learn-status"), getErrorMessage(error), "error");
    setStatus($("quiz-status"), getErrorMessage(error), "error");
  }
}

bootstrap();
