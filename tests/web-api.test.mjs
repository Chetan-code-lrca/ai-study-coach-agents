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

function request(prompt = "Summarize these study notes.", ip = "198.51.100.77") {
  return {
    method: "POST",
    headers: { "x-forwarded-for": ip },
    body: {
      systemPrompt: "You are a careful study coach.",
      messages: [{ role: "user", content: { type: "text", text: prompt } }],
      maxTokens: 1200,
      temperature: 0.3,
    },
  };
}

async function withEnv(overrides, callback) {
  const previous = new Map();
  for (const [key, value] of Object.entries(overrides)) {
    previous.set(key, process.env[key]);
    if (value === null) delete process.env[key];
    else process.env[key] = value;
  }
  try {
    return await callback();
  } finally {
    for (const [key, value] of previous) {
      if (value === undefined) delete process.env[key];
      else process.env[key] = value;
    }
  }
}

test("web AI endpoint rejects methods other than POST", async () => {
  const res = mockResponse();
  await handler({ method: "GET", headers: {} }, res);
  assert.equal(res.statusCode, 405);
  assert.equal(res.headers.Allow, "POST");
});

test("web AI endpoint gives a safe setup message when OpenRouter key is missing", async () => {
  await withEnv({ OPENROUTER_API_KEY: null }, async () => {
    const res = mockResponse();
    await handler(request(), res);
    assert.equal(res.statusCode, 503);
    assert.match(res.body.error, /OPENROUTER_API_KEY/);
    assert.doesNotMatch(JSON.stringify(res.body), /test-only-not-real/);
  });
});

test("web AI endpoint forwards prompts server-side to OpenRouter's free router", async () => {
  const previousFetch = globalThis.fetch;
  await withEnv({
    OPENROUTER_API_KEY: "test-only-not-real",
    OPENROUTER_MODEL: null,
  }, async () => {
    let observed;
    globalThis.fetch = async (url, options) => {
      observed = { url: String(url), options };
      return {
        ok: true,
        status: 200,
        async json() {
          return {
            model: "example/free-model",
            choices: [{ message: { content: "A concise study summary." }, finish_reason: "stop" }],
          };
        },
      };
    };
    try {
      const res = mockResponse();
      await handler(request("Summarize my notes.", "198.51.100.78"), res);
      assert.equal(res.statusCode, 200);
      assert.equal(res.body.text, "A concise study summary.");
      assert.equal(res.body.model, "example/free-model");
      assert.equal(observed.url, "https://openrouter.ai/api/v1/chat/completions");
      assert.equal(observed.options.method, "POST");
      assert.equal(observed.options.headers.Authorization, "Bearer test-only-not-real");
      assert.equal(observed.options.headers["Content-Type"], "application/json");
      assert.equal(observed.options.headers["HTTP-Referer"], "https://ai-study-coach-agents.vercel.app");
      assert.equal(observed.options.headers["X-OpenRouter-Title"], "AI Study Coach");
      const sent = JSON.parse(observed.options.body);
      assert.equal(sent.model, "openrouter/free");
      assert.equal(sent.messages[0].role, "system");
      assert.equal(sent.messages[0].content, "You are a careful study coach.");
      assert.equal(sent.messages[1].role, "user");
      assert.equal(sent.messages[1].content, "Summarize my notes.");
      assert.equal(sent.temperature, 0.3);
      assert.equal(sent.max_tokens, 1200);
      assert.ok(!JSON.stringify(res.body).includes("test-only-not-real"));
    } finally {
      globalThis.fetch = previousFetch;
    }
  });
});

test("web AI endpoint supports a configured model and requests JSON mode when needed", async () => {
  const previousFetch = globalThis.fetch;
  await withEnv({
    OPENROUTER_API_KEY: "test-only-not-real",
    OPENROUTER_MODEL: "example/model:free",
  }, async () => {
    let sent;
    globalThis.fetch = async (_url, options) => {
      sent = JSON.parse(options.body);
      return {
        ok: true,
        status: 200,
        async json() {
          return { choices: [{ message: { content: "{\"ok\":true}" } }] };
        },
      };
    };
    try {
      const res = mockResponse();
      await handler(request("Return valid JSON only with this exact shape: { ok: boolean }", "198.51.100.79"), res);
      assert.equal(res.statusCode, 200);
      assert.equal(sent.model, "example/model:free");
      assert.deepEqual(sent.response_format, { type: "json_object" });
      assert.equal(res.body.text, "{\"ok\":true}");
      assert.equal(res.body.model, "example/model:free");
    } finally {
      globalThis.fetch = previousFetch;
    }
  });
});

test("web AI endpoint handles OpenRouter auth, quota, and availability errors safely", async () => {
  const previousFetch = globalThis.fetch;
  await withEnv({ OPENROUTER_API_KEY: "test-only-not-real" }, async () => {
    const cases = [
      { upstreamStatus: 401, expectedStatus: 502, message: /key was rejected/i },
      { upstreamStatus: 402, expectedStatus: 402, message: /free-model access is unavailable/i },
      { upstreamStatus: 429, expectedStatus: 429, message: /rate limit/i },
      { upstreamStatus: 503, expectedStatus: 503, message: /no compatible free model/i },
    ];
    try {
      for (const item of cases) {
        globalThis.fetch = async () => ({
          ok: false,
          status: item.upstreamStatus,
          async json() { return { error: { message: "private upstream detail" } }; },
        });
        const res = mockResponse();
        await handler(request("Summarize my notes.", `198.51.100.${80 + cases.indexOf(item)}`), res);
        assert.equal(res.statusCode, item.expectedStatus);
        assert.match(res.body.error, item.message);
        assert.ok(!JSON.stringify(res.body).includes("private upstream detail"));
        assert.ok(!JSON.stringify(res.body).includes("test-only-not-real"));
      }
    } finally {
      globalThis.fetch = previousFetch;
    }
  });
});

test("web AI endpoint validates JSON input before making provider calls", async () => {
  await withEnv({ OPENROUTER_API_KEY: "test-only-not-real" }, async () => {
    const previousFetch = globalThis.fetch;
    globalThis.fetch = async () => { throw new Error("fetch must not run for invalid input"); };
    try {
      const res = mockResponse();
      await handler({ ...request(), body: "{not-json" }, res);
      assert.equal(res.statusCode, 400);
      assert.match(res.body.error, /JSON object/);
    } finally {
      globalThis.fetch = previousFetch;
    }
  });
});

test("web AI endpoint enforces a prompt-size limit before provider calls", async () => {
  await withEnv({ OPENROUTER_API_KEY: "test-only-not-real" }, async () => {
    const previousFetch = globalThis.fetch;
    globalThis.fetch = async () => { throw new Error("fetch must not run for oversized prompts"); };
    try {
      const res = mockResponse();
      await handler(request("x".repeat(45_001), "198.51.100.90"), res);
      assert.equal(res.statusCode, 413);
      assert.match(res.body.error, /too large/i);
    } finally {
      globalThis.fetch = previousFetch;
    }
  });
});
