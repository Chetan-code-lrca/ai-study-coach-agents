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

test("retired AI endpoint rejects methods other than POST", async () => {
  const res = mockResponse();
  await handler({ method: "GET", headers: {} }, res);
  assert.equal(res.statusCode, 405);
  assert.equal(res.headers.Allow, "POST");
});

test("retired AI endpoint cannot call an external provider or use an API key", async () => {
  const previousFetch = globalThis.fetch;
  globalThis.fetch = async () => {
    throw new Error("The retired endpoint must never make network requests.");
  };
  try {
    const res = mockResponse();
    await handler({
      method: "POST",
      headers: {},
      body: { messages: [{ role: "user", content: "hello" }] },
    }, res);
    assert.equal(res.statusCode, 410);
    assert.match(res.body.error, /built-in offline study tools/i);
    assert.match(res.body.error, /does not require an external AI API key/i);
  } finally {
    globalThis.fetch = previousFetch;
  }
});
