// Browser-only adapter for the Vercel edition.
// All study generation runs locally in this browser; no external AI API is called.
import { generateOfflineStudyResponse } from "./offline-study.js";

window.__STUDY_COACH_WEB__ = true;

const storageKey = (key) => "ai-study-coach-web:" + String(key);

export const AnnaAppRuntime = {
  async connect() {
    return {
      llm: {
        async complete(payload) {
          const text = generateOfflineStudyResponse(payload);
          if (typeof text !== "string" || !text.trim()) {
            throw new Error("The built-in offline study tools could not produce a result for this input.");
          }
          return { content: text, model: "offline-study-tools" };
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
