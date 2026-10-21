// Adapter for the browser-hosted edition. The native Anna app keeps using
// the official Anna App Runtime; this adapter stores records in this browser
// and sends AI requests to the server-side /api/study endpoint.
window.__STUDY_COACH_WEB__ = true;

const storageKey = (key) => `ai-study-coach-web:${String(key)}`;

export const AnnaAppRuntime = {
  async connect() {
    return {
      llm: {
        async complete(payload) {
          const response = await fetch("/api/study", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            cache: "no-store",
            body: JSON.stringify(payload),
          });
          let data;
          try {
            data = await response.json();
          } catch {
            throw new Error("The web AI service returned an invalid response. Please try again.");
          }
          if (!response.ok) {
            throw new Error(data?.error || `AI request failed (${response.status}).`);
          }
          if (typeof data?.text !== "string" || !data.text.trim()) {
            throw new Error("The AI service returned an empty response. Please try again.");
          }
          return { content: data.text, model: data.model || "Gemini" };
        },
      },
      storage: {
        async get({ key }) {
          const raw = localStorage.getItem(storageKey(key));
          if (raw === null) return null;
          try {
            return { value: JSON.parse(raw) };
          } catch {
            throw new Error("Saved browser data could not be read. Clear this app's local storage only if you are comfortable losing its saved history.");
          }
        },
        async set({ key, value }) {
          try {
            localStorage.setItem(storageKey(key), JSON.stringify(value));
            return { ok: true };
          } catch (error) {
            if (error?.name === "QuotaExceededError") {
              throw new Error("This browser's storage is full. Remove older saved notes or clear some browser storage before saving again.");
            }
            throw error;
          }
        },
      },
      window: {
        async set_title({ title }) {
          if (typeof title === "string" && title.trim()) document.title = title.trim();
        },
      },
    };
  },
};
