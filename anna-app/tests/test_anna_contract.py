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
        self.assertIn("anna.llm.complete", self.bundle_javascript)
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
        self.assertEqual(self.package["dependencies"]["pdfjs-dist"], "6.4.299")
        self.assertEqual(self.package["dependencies"]["mammoth"], "1.13.0")
        self.assertEqual(self.package["devDependencies"]["esbuild"], "0.28.2")
        self.assertIn('from "pdfjs-dist/build/pdf.mjs"', self.javascript)
        self.assertIn('from "mammoth"', self.javascript)
        self.assertIn('new URL("./pdf.worker.min.mjs", import.meta.url)', self.javascript)
        self.assertIn('"pdf.worker.min.mjs"', self.build_script)
        self.assertTrue((APP_ROOT / "bundle" / "pdf.worker.min.mjs").is_file())

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

    def test_runtime_status_and_errors_remain_visible(self) -> None:
        self.assertIn("Working with Anna's model", self.javascript)
        self.assertIn('role="status"', self.html)
        self.assertIn('id="learn-status"', self.html)
        self.assertIn('id="plan-status"', self.html)
        self.assertIn('id="quiz-status"', self.html)


if __name__ == "__main__":
    unittest.main()
