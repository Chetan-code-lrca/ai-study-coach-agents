from __future__ import annotations

import json
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]


class AnnaContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = json.loads((APP_ROOT / "app.json").read_text(encoding="utf-8"))
        cls.manifest = json.loads((APP_ROOT / "manifest.json").read_text(encoding="utf-8"))
        cls.package = json.loads((APP_ROOT / "package.json").read_text(encoding="utf-8"))
        cls.build_script = (APP_ROOT / "scripts" / "build.mjs").read_text(encoding="utf-8")
        cls.html = (APP_ROOT / "bundle" / "index.html").read_text(encoding="utf-8")
        cls.javascript = (APP_ROOT / "src" / "app.js").read_text(encoding="utf-8")
        cls.prompts = (APP_ROOT / "src" / "study-prompts.js").read_text(encoding="utf-8")
        cls.bundle_javascript = (APP_ROOT / "bundle" / "app.js").read_text(encoding="utf-8")
        cls.css = (APP_ROOT / "bundle" / "style.css").read_text(encoding="utf-8")

    def test_app_uses_direct_host_llm_without_bundled_executa(self) -> None:
        self.assertNotIn("bundled_executas", self.app)
        self.assertEqual(self.manifest["required_executas"], [])
        self.assertEqual(self.manifest["optional_executas"], [])
        host_api = self.manifest["ui"]["host_api"]
        self.assertEqual(host_api["llm"], ["complete"])
        self.assertEqual(host_api["storage"], ["get", "set"])
        self.assertEqual(host_api["window"], ["set_title"])
        self.assertNotIn("tools", host_api)

    def test_frontend_calls_direct_llm_api_and_never_invokes_executa(self) -> None:
        self.assertIn("anna.llm.complete", self.javascript)
        self.assertNotIn("anna.tools.invoke", self.javascript)
        self.assertNotIn("EXECUTA_TOOL_ID", self.javascript)
        self.assertNotIn("tool-dev-ai-study-coach", self.javascript)
        self.assertIn("buildStudyRequest(action, payload)", self.javascript)
        self.assertIn("extractCompletionText(reply)", self.javascript)
        self.assertIn("systemPrompt: request.systemPrompt", self.javascript)
        self.assertIn("maxTokens: request.maxTokens", self.javascript)
        self.assertIn(".llm.complete(", self.bundle_javascript)
        self.assertNotIn("anna.tools.invoke", self.bundle_javascript)

    def test_frontend_does_not_require_provider_api_keys(self) -> None:
        self.assertNotIn("GOOGLE_API_KEY", self.javascript)
        self.assertNotIn("google-genai", self.javascript)
        self.assertNotIn("GEMINI_API_KEY", self.javascript)

    def test_manifest_grants_only_host_apis_the_frontend_uses(self) -> None:
        self.assertEqual(self.manifest["ui"]["bundle"]["external_origins"], [])
        self.assertNotIn("csp_overrides", self.manifest["ui"])
        self.assertEqual(self.manifest["ui"]["host_api"]["llm"], ["complete"])
        self.assertEqual(self.manifest["ui"]["host_api"]["storage"], ["get", "set"])
        self.assertEqual(self.manifest["ui"]["host_api"]["window"], ["set_title"])

    def test_file_drop_zone_supports_local_study_documents(self) -> None:
        for element_id in ("file-drop-zone", "file-input", "choose-files-btn", "use-for-quiz-btn"):
            self.assertIn(f'id="{element_id}"', self.html)
        for extension in ("pdf", "docx", "txt", "md", "csv", "json"):
            self.assertIn(f'"{extension}"', self.javascript)
        self.assertIn("extractPdfText(file)", self.javascript)
        self.assertIn("mammoth.extractRawText", self.javascript)
        self.assertIn("MAX_FILE_BYTES = 10 * 1024 * 1024", self.javascript)
        self.assertIn("MAX_MATERIAL_CHARS = 30000", self.javascript)
        self.assertIn("text is sent to Anna only when you request an AI action", self.html)

    def test_document_parsers_are_pinned_and_bundled_locally(self) -> None:
        self.assertEqual(self.package["dependencies"]["katex"], "0.19.0")
        self.assertEqual(self.package["dependencies"]["pdfjs-dist"], "6.4.299")
        self.assertEqual(self.package["dependencies"]["mammoth"], "1.13.0")
        self.assertEqual(self.package["devDependencies"]["esbuild"], "0.28.2")
        self.assertIn('from "pdfjs-dist/build/pdf.mjs"', self.javascript)
        self.assertIn('from "mammoth"', self.javascript)
        self.assertIn('new URL("./pdf.worker.min.mjs", import.meta.url)', self.javascript)
        self.assertIn('"pdf.worker.min.mjs"', self.build_script)
        self.assertIn('"katex.min.css"', self.build_script)
        self.assertIn('"fonts"', self.build_script)
        self.assertIn('href="./katex.min.css"', self.html)
        self.assertTrue((APP_ROOT / "bundle" / "pdf.worker.min.mjs").is_file())
        self.assertTrue((APP_ROOT / "bundle" / "katex.min.css").is_file())
        self.assertTrue((APP_ROOT / "bundle" / "fonts" / "KaTeX_Main-Regular.woff2").is_file())

    def test_markdown_renderer_typesets_math_with_trusted_local_katex(self) -> None:
        markdown = (APP_ROOT / "src" / "markdown.js").read_text(encoding="utf-8")
        self.assertIn('import katex from "katex"', markdown)
        self.assertIn("katex.renderToString", markdown)
        self.assertIn("throwOnError: false", markdown)
        self.assertIn("trust: false", markdown)
        self.assertIn("math-display", self.css)
        self.assertIn(".markdown-result .katex", self.css)

    def test_pdf_cleanup_uses_the_documented_loading_task_api(self) -> None:
        self.assertIn("const loadingTask = pdfjs.getDocument", self.javascript)
        self.assertIn("await loadingTask.destroy();", self.javascript)
        self.assertNotIn("await pdf.destroy()", self.javascript)

    def test_prompts_are_client_side_and_unicode_safe(self) -> None:
        self.assertIn("export function buildStudyRequest", self.prompts)
        self.assertIn("untrusted reference data", self.prompts)
        self.assertIn("MAX_MATERIAL_CHARS = 30000", self.prompts)
        self.assertIn("anna.llm.complete", self.javascript)
        # Direct calls keep document text in the frontend-to-host path instead
        # of serializing it through a Windows Python Executa subprocess.
        self.assertNotIn("sys.stdout", self.javascript)
        self.assertNotIn("sampling/createMessage", self.javascript)

    def test_quiz_and_typography_regressions_remain_covered(self) -> None:
        self.assertIn('label.classList.add("quiz-option-incorrect")', self.javascript)
        self.assertIn('label.classList.add("quiz-option-correct")', self.javascript)
        self.assertIn(".quiz-option-incorrect { border-color:", self.css)
        self.assertIn("background: #fff0ef", self.css)
        self.assertIn(".quiz-option-correct { border-color:", self.css)
        self.assertIn("font-size: 15px;", self.css)
        self.assertIn("font-size: clamp(25px, 4vw, 35px);", self.css)

    def test_study_profile_is_persisted_with_user_activity(self) -> None:
        for element_id in (
            "profile-form",
            "profile-name",
            "profile-course",
            "profile-year",
            "profile-goal",
            "profile-hours",
            "profile-focus",
            "profile-save-btn",
            "profile-status",
            "profile-setup-btn",
        ):
            self.assertIn(f'id="{element_id}"', self.html)
        self.assertIn('data-page="profile"', self.html)
        self.assertIn("Anna handles account sign-in", self.html)
        self.assertIn("does not ask for or store a password", self.html)
        self.assertIn("state.profile = normalizeProfile(value.profile)", self.javascript)
        self.assertIn("profile: state.profile", self.javascript)
        self.assertIn("key: STORAGE_KEY", self.javascript)
        self.assertIn("dailyHours", self.javascript)
        self.assertIn("state.profile.primaryGoal", self.javascript)
        self.assertIn("state.profile.focusAreas", self.javascript)

    def test_first_run_profile_prompt_is_hidden_after_profile_load(self) -> None:
        self.assertIn('id="profile-prompt" hidden', self.html)
        self.assertIn('$("profile-prompt").hidden = Boolean(profile?.displayName)', self.javascript)
        self.assertIn("Welcome back,", self.javascript)
        self.assertIn("Your study goals and activity are saved with this Anna app.", self.javascript)

    def test_existing_history_and_profile_share_the_same_storage_record(self) -> None:
        self.assertIn("if (Array.isArray(value.studyPlans)) state.studyPlans = value.studyPlans", self.javascript)
        self.assertIn("if (Array.isArray(value.quizHistory)) state.quizHistory = value.quizHistory", self.javascript)
        self.assertIn("studyPlans: state.studyPlans.slice(-50)", self.javascript)
        self.assertIn("quizHistory: state.quizHistory.slice(-100)", self.javascript)
        self.assertIn("profile: state.profile", self.javascript)
        self.assertIn("await anna.storage.get({ key: STORAGE_KEY })", self.javascript)
        self.assertIn("await anna.storage.set({", self.javascript)

    def test_runtime_status_and_errors_remain_visible(self) -> None:
        self.assertIn("Working with Anna's model", self.javascript)
        self.assertIn('role="status"', self.html)
        self.assertIn('id="learn-status"', self.html)
        self.assertIn('id="plan-status"', self.html)
        self.assertIn('id="quiz-status"', self.html)


if __name__ == "__main__":
    unittest.main()
