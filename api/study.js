const WINDOW_MS = 60_000;
const LIMIT_PER_WINDOW = 15;
// Best-effort per-instance rate limit. Configure provider quotas and monitor
// usage as well; serverless memory is not a globally shared rate limiter.
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

  const apiKey = process.env.GOOGLE_API_KEY;
  if (!apiKey) {
    return res.status(503).json({
      error: "The web AI service is not configured yet. The site owner must add GOOGLE_API_KEY in Vercel Project Settings → Environment Variables, then redeploy.",
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

  const model = String(process.env.GEMINI_MODEL || "gemini-3.8-flash").trim();
  const generationConfig = {
    temperature: Number.isFinite(Number(body.temperature))
      ? Math.min(1, Math.max(0, Number(body.temperature)))
      : 0.3,
    maxOutputTokens: clampTokens(body.maxTokens),
  };
  if (/Return valid JSON only|valid JSON only with this exact shape/i.test(prompt)) {
    generationConfig.responseMimeType = "application/json";
  }

  try {
    const upstream = await fetch(
      `https://generativelanguage.googleapis.com/v1beta/models/${encodeURIComponent(model)}:generateContent`,
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-goog-api-key": apiKey,
        },
        body: JSON.stringify({
          systemInstruction: systemPrompt ? { parts: [{ text: systemPrompt }] } : undefined,
          contents: [{ role: "user", parts: [{ text: prompt }] }],
          generationConfig,
        }),
        signal: AbortSignal.timeout(25_000),
      },
    );

    const data = await upstream.json().catch(() => ({}));
    if (!upstream.ok) {
      if (upstream.status === 429) {
        return res.status(429).json({ error: "The AI provider quota is temporarily busy. Wait a moment and retry." });
      }
      console.error("Gemini request failed", { status: upstream.status, model, message: data?.error?.message });
      return res.status(502).json({
        error: upstream.status === 401 || upstream.status === 403
          ? "The server-side Gemini key was rejected. Check GOOGLE_API_KEY in Vercel and redeploy."
          : "The AI provider could not complete this request. Check the configured model and provider quota, then retry.",
      });
    }

    const result = data?.candidates?.[0]?.content?.parts
      ?.filter((part) => typeof part.text === "string")
      .map((part) => part.text)
      .join("\n")
      .trim();
    if (!result) {
      console.error("Gemini returned no text", { model, finishReason: data?.candidates?.[0]?.finishReason });
      return res.status(502).json({ error: "The AI provider returned no text. Please shorten the request and try again." });
    }
    return res.status(200).json({ text: result, model });
  } catch (error) {
    console.error("Gemini request error", { model, message: error?.message || String(error) });
    return res.status(504).json({ error: "The AI request timed out or the provider was unreachable. Please try again." });
  }
}
