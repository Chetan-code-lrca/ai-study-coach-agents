import assert from "node:assert/strict";
import test from "node:test";
import { prepareHistoryForStorage } from "../src/history-store.js";

test("keeps full text for the most recent plans and metadata for older plans", () => {
  const plans = Array.from({ length: 8 }, (_unused, index) => ({
    subject: `Subject ${index}`,
    createdAt: String(index),
    planText: `Complete plan ${index}`,
  }));
  const saved = prepareHistoryForStorage(plans, "plan", 50, 3);
  assert.equal(saved.length, 8);
  assert.equal(saved[0].subject, "Subject 0");
  assert.equal("planText" in saved[0], false);
  assert.equal("planText" in saved[4], false);
  assert.equal(saved[5].planText, "Complete plan 5");
  assert.equal(saved[7].planText, "Complete plan 7");
});

test("bounds plan text and marks truncated plan history", () => {
  const text = "P".repeat(15000);
  const saved = prepareHistoryForStorage([{ subject: "CS", planText: text }], "plan", 50);
  assert.equal(saved[0].planText.length, 14000);
  assert.equal(saved[0].planTextTruncated, true);
});

test("keeps details for recent quiz attempts and strips older answer payloads", () => {
  const quizzes = Array.from({ length: 7 }, (_unused, index) => ({
    title: `Quiz ${index}`,
    score: index,
    total: 5,
    questions: [{ question: `Question ${index}` }],
    answers: [index % 4],
  }));
  const saved = prepareHistoryForStorage(quizzes, "quiz", 100, 2);
  assert.equal(saved.length, 7);
  assert.equal("questions" in saved[4], false);
  assert.equal("answers" in saved[4], false);
  assert.deepEqual(saved[5].questions, [{ question: "Question 5" }]);
  assert.deepEqual(saved[6].answers, [2]);
  assert.equal(saved[0].score, 0);
});

test("caps stored history length without mutating in-memory history", () => {
  const plans = Array.from({ length: 60 }, (_unused, index) => ({ subject: String(index), planText: "text" }));
  const saved = prepareHistoryForStorage(plans, "plan", 50, 6);
  assert.equal(saved.length, 50);
  assert.equal(saved[0].subject, "10");
  assert.equal("planText" in plans[0], true);
  assert.equal("planText" in saved[0], false);
});

test("keeps note metadata while retaining content for only the most recent saved notes", () => {
  const notes = Array.from({ length: 7 }, (_unused, index) => ({
    id: `note-${index}`,
    title: `Notes ${index}`,
    material: `Full note text ${index}`,
    createdAt: String(index),
    materialTruncated: false,
  }));
  const saved = prepareHistoryForStorage(notes, "note", 50, 2);
  assert.equal(saved.length, 7);
  assert.equal(saved[0].id, "note-0");
  assert.equal(saved[0].title, "Notes 0");
  assert.equal("material" in saved[4], false);
  assert.equal(saved[5].material, "Full note text 5");
  assert.equal(saved[6].material, "Full note text 6");
});

test("bounds long saved note text and preserves note-link metadata on quiz history", () => {
  const note = { id: "note-long", title: "Long notes", material: "N".repeat(12000) };
  const savedNote = prepareHistoryForStorage([note], "note", 50);
  assert.equal(savedNote[0].material.length, 10000);
  assert.equal(savedNote[0].materialTruncated, true);

  const quizzes = [{ title: "Quiz", sourceNoteId: "note-1", sourceNoteTitle: "Operating Systems", questions: [1], answers: [0] }];
  const savedQuiz = prepareHistoryForStorage(quizzes, "quiz", 100, 0);
  assert.equal(savedQuiz[0].sourceNoteId, "note-1");
  assert.equal(savedQuiz[0].sourceNoteTitle, "Operating Systems");
  assert.equal("questions" in savedQuiz[0], false);
});
