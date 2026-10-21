import assert from "node:assert/strict";
import test from "node:test";
import handler from "../api/study.js";

function mockResponse() {
  return {
    statusCode: 200,
    headers: {},
    body: null,
    setHeader(name, value) { this.headers[name] = value; },
    status(code) { this.statusCode = code; return this; },
    json(value) { this.body = value; return this; },
  };
}

function request(prompt = "Summarize these study notes.") {
  return {
    method: "POST",
    headers: { "x-forwarded-for": "198.51.100.77" },
    body: {
      systemPrompt: "You are a careful study coach.",
      messages: [{ role: "user", content: { type: "text", text: prompt } }],
      maxTokens: 1200,
      temperature: 0.3,
    },
  };
}

test("web AI endpoint rejects methods other than POST", async () => {
  const res = mockResponse();
  await handler({ method: "GET", headers: {} }, res);
  assert.equal(res.statusCode, 405);
  assert.equal(res.headers.Allow, "POST");
});

test("web AI endpoint gives a safe setup message when the server key is missing", async () => {
  const previous = process.env.GOOGLE_API_KEY;
  delete process.env.GOOGLE_API_KEY;
  try {
    const res = mockResponse();
    await handler(request(), res);
    assert.equal(res.statusCode, 503);
    assert.match(res.body.error, /GOOGLE_API_KEY/);
    assert.doesNotMatch(JSON.stringify(res.body), /test-only-not-real/);
  } finally {
    if (previous === undefined) delete process.env.GOOGLE_API_KEY;
    else process.env.GOOGLE_API_KEY = previous;
  }
});

test("web AI endpoint forwards prompts server-side and returns generated text", async () => {
  const previousKey = process.env.GOOGLE_API_KEY;
  const previousModel = process.env.GEMINI_MODEL;
  const previousFetch = globalThis.fetch;
  process.env.GOOGLE_API_KEY = "test-only-not-real";
  process.env.GEMINI_MODEL = "gemini-3.8-flash";
  let observed;
  globalThis.fetch = async (url, options) => {
    observed = { url: String(url), options };
    return {
      ok: true,
      status: 200,
      async json() {
        return { candidates: [{ content: { parts: [{ text: "A concise study summary." }] } }] };
      },
    };
  };
  try {
    const res = mockResponse();
    await handler(request("Summarize my notes."), res);
    assert.equal(res.statusCode, 200);
    assert.equal(res.body.text, "A concise study summary.");
    assert.equal(res.body.model, "gemini-3.8-flash");
    assert.match(observed.url, /gemini-3\.8-flash:generateContent/);
    assert.equal(observed.options.headers["x-goog-api-key"], "test-only-not-real");
    const sent = JSON.parse(observed.options.body);
    assert.equal(sent.systemInstruction.parts[0].text, "You are a careful study coach.");
    assert.equal(sent.contents[0].parts[0].text, "Summarize my notes.");
    assert.ok(!JSON.stringify(res.body).includes("test-only-not-real"));
  } finally {
    globalThis.fetch = previousFetch;
    if (previousKey === undefined) delete process.env.GOOGLE_API_KEY;
    else process.env.GOOGLE_API_KEY = previousKey;
    if (previousModel === undefined) delete process.env.GEMINI_MODEL;
    else process.env.GEMINI_MODEL = previousModel;
  }
});

test("web AI endpoint enforces a prompt-size limit before provider calls", async () => {
  const previous = process.env.GOOGLE_API_KEY;
  process.env.GOOGLE_API_KEY = "test-only-not-real";
  const previousFetch = globalThis.fetch;
  globalThis.fetch = async () => { throw new Error("fetch must not run for oversized prompts"); };
  try {
    const res = mockResponse();
    await handler(request("x".repeat(45_001)), res);
    assert.equal(res.statusCode, 413);
    assert.match(res.body.error, /too large/i);
  } finally {
    globalThis.fetch = previousFetch;
    if (previous === undefined) delete process.env.GOOGLE_API_KEY;
    else process.env.GOOGLE_API_KEY = previous;
  }
});
