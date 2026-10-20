import { AnnaAppRuntime } from "/static/anna-apps/_sdk/latest/index.js";

const EXECUTA_HANDLE = "study-coach";
const EXECUTA_TOOL_ID =
  (typeof window !== "undefined" &&
    window.__ANNA_TOOL_IDS__ &&
    window.__ANNA_TOOL_IDS__[EXECUTA_HANDLE]) ||
  "tool-dev-ai-study-coach";
const STORAGE_KEY = "ai-study-coach:activity:v1";

const $ = (id) => document.getElementById(id);
const state = {
  studyPlans: [],
  quizHistory: [],
  currentQuiz: null,
  answers: {},
  quizSubmitted: false,
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
  if (/SAMPLING_NOT_GRANTED|SAMPLING_NOT_NEGOTIATED|NOT_NEGOTIATED/i.test(message)) {
    return "Anna LLM sampling is not enabled for this Executa yet. Check the app/Executa sampling permissions in Anna, then try again.";
  }
  if (/timeout|timed out/i.test(message)) {
    return "The request took too long. Try again with shorter notes or a smaller request.";
  }
  return message;
}

async function invokeStudyCoach(action, payload) {
  if (!anna) throw new Error("Anna runtime is not connected. Open this app inside the Anna App Harness and retry.");
  const result = await anna.tools.invoke({
    tool_id: EXECUTA_TOOL_ID,
    method: "study_coach",
    args: { action, ...payload },
  });
  if (result?.success === false) {
    throw new Error(result.error || "The study request failed.");
  }
  const data = result?.data && typeof result.data === "object" && typeof result.data.text === "string"
    ? result.data
    : result;
  if (data?.success === false) throw new Error(data.error || "The study request failed.");
  if (!data || typeof data.text !== "string" || !data.text.trim()) {
    throw new Error("Anna returned an empty response. Please try again.");
  }
  return data;
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
    const data = await invokeStudyCoach(action, payload);
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
  textElement.textContent = text;
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

$("material-text").addEventListener("input", () => {
  $("material-count").textContent = `${$("material-text").value.length.toLocaleString()} / 30,000 characters`;
});

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
    const text = target?.querySelector(".result-text")?.textContent || target?.textContent || "";
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
