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
