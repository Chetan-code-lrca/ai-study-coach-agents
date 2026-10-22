import assert from "node:assert/strict";
import test from "node:test";
import { generateOfflineStudyResponse } from "../web-app/offline-study.js";

function payload(prompt) {
  return {
    systemPrompt: "Offline study test",
    messages: [{ role: "user", content: { type: "text", text: prompt } }],
  };
}

const sourceBlock = [
  "<study_material>",
  "Supervised Learning — uses labelled examples to learn an input-output mapping.",
  "Unsupervised Learning — discovers patterns in unlabelled data.",
  "Regression — predicts a continuous numerical value.",
  "Classification — predicts a category or class label.",
  "</study_material>"
].join("\n");

test("offline study plan respects the selected duration and daily time", () => {
  const prompt = [
    "Create a practical, specific study plan for a student.",
    "Subject: Machine Learning",
    "Current level: Intermediate",
    "Duration: 2 weeks",
    "Available study time: 1 hours per day",
    "Learning goals: Prepare for the semester exam.",
    "Use the supplied notes to prioritize topics.",
    sourceBlock
  ].join("\n");
  const text = generateOfflineStudyResponse(payload(prompt));
  assert.match(text, /Offline mode/);
  assert.match(text, /Week 1/);
  assert.match(text, /Week 2/);
  assert.match(text, /Weekly checkpoint/);
  assert.match(text, /Supervised Learning/);
  assert.match(text, /60 min/);
});

test("offline quiz returns the exact requested count and valid four-option schema", () => {
  const prompt = [
    "Create exactly 5 multiple-choice questions about Machine Learning at Medium difficulty.",
    "All questions and correct answers must be grounded in the supplied source material.",
    'Return valid JSON only with this exact shape: {"title":"string","questions":[{"question":"string","options":["A","B","C","D"],"correct_index":0,"explanation":"string"}]}',
    sourceBlock
  ].join("\n");
  const raw = generateOfflineStudyResponse(payload(prompt));
  const quiz = JSON.parse(raw);
  assert.equal(quiz.questions.length, 5);
  assert.match(quiz.title, /Offline note-based quiz/);
  for (const question of quiz.questions) {
    assert.equal(question.options.length, 4);
    assert.equal(new Set(question.options).size, 4);
    assert.ok(Number.isInteger(question.correct_index));
    assert.ok(question.correct_index >= 0 && question.correct_index <= 3);
    assert.ok(question.question.length > 0);
    assert.ok(question.explanation.length > 0);
  }
});

test("topic-only offline quiz uses the built-in subject question bank", () => {
  const prompt = "Create exactly 3 multiple-choice questions about Machine Learning at Easy difficulty.\nReturn valid JSON only with this exact shape:";
  const quiz = JSON.parse(generateOfflineStudyResponse(payload(prompt)));
  assert.equal(quiz.questions.length, 3);
  assert.match(quiz.title, /Machine Learning/);
  assert.match(quiz.questions[0].question, /labelled examples/i);
});

test("offline summary extracts key concepts without calling a provider", () => {
  const prompt = [
    "Summarize the supplied document as if the student asked you to read it and explain what matters.",
    "Return a useful, source-grounded study summary with these sections:",
    sourceBlock
  ].join("\n");
  const text = generateOfflineStudyResponse(payload(prompt));
  assert.match(text, /Offline study summary/);
  assert.match(text, /Supervised Learning/);
  assert.match(text, /Self-test questions/);
  assert.match(text, /external AI API/);
});

test("offline concept explanation uses matched terms from the source", () => {
  const prompt = [
    "Teach the most important concepts from the supplied material in a way a student can understand and revise.",
    sourceBlock
  ].join("\n");
  const text = generateOfflineStudyResponse(payload(prompt));
  assert.match(text, /Explain concepts — offline mode/);
  assert.match(text, /Unsupervised Learning/);
  assert.match(text, /labelled data|unlabelled data/i);
});

test("offline question answering returns matching source excerpts and admits a miss", () => {
  const prompt = [
    "Answer the student's question using the supplied study material as the primary and authoritative source.",
    sourceBlock,
    "Student's question:",
    "What is supervised learning?"
  ].join("\n");
  const text = generateOfflineStudyResponse(payload(prompt));
  assert.match(text, /Answer from your notes — offline mode/);
  assert.match(text, /Supervised Learning/);

  const unmatched = generateOfflineStudyResponse(payload([
    "Answer the student's question using the supplied study material as the primary and authoritative source.",
    sourceBlock,
    "Student's question:",
    "What is quantum teleportation?"
  ].join("\n")));
  assert.match(unmatched, /could not find a clear keyword match/i);
});

test("offline handler rejects unsupported study requests clearly", () => {
  assert.throws(
    () => generateOfflineStudyResponse(payload("Do something unsupported.")),
    /not supported by the built-in offline study tools/i
  );
});
