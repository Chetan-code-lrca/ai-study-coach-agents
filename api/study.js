const WINDOW_MS = 60_000;
const LIMIT_PER_WINDOW = 15;
// Best-effort per-instance rate limit. OpenRouter also enforces free-tier
// account limits; this in-memory guard is not a global or daily quota.
const requestLog = new Map();

function allowRequest(ip, now = Date.now()) {
  const current = requestLog.get(ip) || [];
  const recent = current.filter((timestamp) => now - timestamp < WINDOW_MS);
  if (recent.length >= LIMIT_PER_WINDOW) {
    requestLog.set(ip, recent);
    return false;
  }
  recent.push(now);
  requestLog.set(ip, recent);
  if (requestLog.size > 5000) {
    for (const [key, timestamps] of requestLog) {
      if (!timestamps.some((timestamp) => now - timestamp < WINDOW_MS)) requestLog.delete(key);
    }
  }
  return true;
}

function textFromMessages(messages) {
  if (!Array.isArray(messages)) return "";
  return messages
    .map((message) => {
      const content = message?.content;
      if (typeof content === "string") return content;
      if (content && typeof content.text === "string") return content.text;
      if (Array.isArray(content)) return content
        .filter((part) => part && typeof part.text === "string")
        .map((part) => part.text)
        .join("\n");
      return "";
    })
    .filter(Boolean)
    .join("\n\n")
    .trim();
}

function textFromCompletion(message) {
  const content = message?.content;
  if (typeof content === "string") return content.trim();
  if (Array.isArray(content)) {
    return content
      .filter((part) => part && typeof part.text === "string")
      .map((part) => part.text)
      .join("\n")
      .trim();
  }
  return "";
}

function clampTokens(value) {
  const tokens = Number(value);
  if (!Number.isFinite(tokens)) return 2500;
  return Math.min(4096, Math.max(256, Math.floor(tokens)));
}

export default async function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("X-Content-Type-Options", "nosniff");

  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "Use POST to request an AI response." });
  }

  const apiKey = process.env.OPENROUTER_API_KEY;
  if (!apiKey) {
    return res.status(503).json({
      error: "The web AI service is not configured yet. Add OPENROUTER_API_KEY in Vercel Project Settings → Environment Variables, then redeploy.",
    });
  }

  let body = req.body;
  if (typeof body === "string") {
    try { body = JSON.parse(body); } catch { body = null; }
  }
  if (!body || typeof body !== "object" || Array.isArray(body)) {
    return res.status(400).json({ error: "The request body must be a JSON object." });
  }

  const prompt = textFromMessages(body.messages);
  const systemPrompt = typeof body.systemPrompt === "string" ? body.systemPrompt.slice(0, 12000) : "";
  if (!prompt) return res.status(400).json({ error: "Enter a study request or some study material first." });
  if (prompt.length > 45_000) {
    return res.status(413).json({ error: "This request is too large. Shorten the study material and try again." });
  }

  const forwarded = String(req.headers["x-forwarded-for"] || req.headers["x-real-ip"] || "unknown");
  const ip = forwarded.split(",")[0].trim().slice(0, 100) || "unknown";
  if (!allowRequest(ip)) {
    return res.status(429).json({ error: "Too many AI requests from this address. Wait a minute before trying again." });
  }

  const model = String(process.env.OPENROUTER_MODEL || "openrouter/free").trim();
  if (model !== "openrouter/free" && !model.endsWith(":free")) {
    return res.status(503).json({
      error: "This deployment is configured for free OpenRouter models only. Set OPENROUTER_MODEL to openrouter/free or a model ID ending in :free.",
    });
  }

  const messages = [];
  if (systemPrompt) messages.push({ role: "system", content: systemPrompt });
  messages.push({ role: "user", content: prompt });

  const payload = {
    model,
    messages,
    temperature: Number.isFinite(Number(body.temperature))
      ? Math.min(1, Math.max(0, Number(body.temperature)))
      : 0.3,
    max_tokens: clampTokens(body.maxTokens),
  };

  // The free-model router selects an available free model that supports
  // required capabilities such as structured output where supported.
  if (/Return valid JSON only|valid JSON only with this exact shape/i.test(prompt)) {
    payload.response_format = { type: "json_object" };
  }

  try {
    const upstream = await fetch("https://openrouter.ai/api/v1/chat/completions", {
      method: "POST",
      headers: {
        "Authorization": `Bearer ${apiKey}`,
        "Content-Type": "application/json",
        "HTTP-Referer": "https://ai-study-coach-agents.vercel.app",
        "X-OpenRouter-Title": "AI Study Coach",
      },
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(25_000),
    });

    const data = await upstream.json().catch(() => ({}));
    if (!upstream.ok) {
      const upstreamMessage = data?.error?.message || data?.message || "unknown provider error";
      console.error("OpenRouter request failed", {
        status: upstream.status,
        model,
        message: String(upstreamMessage).slice(0, 500),
      });

      if (upstream.status === 401 || upstream.status === 403) {
        return res.status(502).json({
          error: "OpenRouter rejected the server-side API key. Check OPENROUTER_API_KEY in Vercel and redeploy.",
        });
      }
      if (upstream.status === 402) {
        return res.status(402).json({
          error: "OpenRouter reports that free-model access is unavailable for this account right now. Check the account's free-tier limits and activity.",
        });
      }
      if (upstream.status === 429) {
        return res.status(429).json({
          error: "OpenRouter's free-model rate limit was reached or providers are busy. Wait a moment and retry.",
        });
      }
      if (upstream.status === 503 || upstream.status >= 500) {
        return res.status(503).json({
          error: "No compatible free model is available right now. Please retry in a little while.",
        });
      }
      return res.status(502).json({
        error: "OpenRouter could not complete this request. Check the configured model and request limits, then retry.",
      });
    }

    const result = textFromCompletion(data?.choices?.[0]?.message);
    if (!result) {
      console.error("OpenRouter returned no text", {
        model: data?.model || model,
        finishReason: data?.choices?.[0]?.finish_reason,
      });
      return res.status(502).json({
        error: "The AI provider returned no text. Please shorten the request and try again.",
      });
    }

    return res.status(200).json({ text: result, model: data?.model || model });
  } catch (error) {
    console.error("OpenRouter request error", {
      model,
      message: error?.message || String(error),
    });
    return res.status(504).json({
      error: "The AI request timed out or the provider was unreachable. Please try again.",
    });
  }
}
