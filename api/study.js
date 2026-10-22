// Retired endpoint: the Vercel browser edition now runs built-in study tools
// in the client. No third-party AI API key is needed or used.
export default function handler(req, res) {
  res.setHeader("Cache-Control", "no-store");
  res.setHeader("X-Content-Type-Options", "nosniff");

  if (req.method !== "POST") {
    res.setHeader("Allow", "POST");
    return res.status(405).json({ error: "Use POST to request an AI response." });
  }

  return res.status(410).json({
    error: "This endpoint is retired. The browser app now uses built-in offline study tools and does not require an external AI API key."
  });
}
