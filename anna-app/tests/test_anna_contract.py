from __future__ import annotations

import json
import sys
import tomllib
import unittest
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
TOOL_DIR = APP_ROOT / "executas" / "study-coach"


class AnnaContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.app = json.loads((APP_ROOT / "app.json").read_text(encoding="utf-8"))
        cls.manifest = json.loads((APP_ROOT / "manifest.json").read_text(encoding="utf-8"))
        cls.executa = json.loads((TOOL_DIR / "executa.json").read_text(encoding="utf-8"))
        cls.pyproject = tomllib.loads((TOOL_DIR / "pyproject.toml").read_text(encoding="utf-8"))
        cls.html = (APP_ROOT / "bundle" / "index.html").read_text(encoding="utf-8")
        cls.javascript = (APP_ROOT / "bundle" / "app.js").read_text(encoding="utf-8")
        cls.css = (APP_ROOT / "bundle" / "style.css").read_text(encoding="utf-8")
        cls.plugin = (TOOL_DIR / "study_coach_plugin.py").read_text(encoding="utf-8")

    def test_bundled_executa_path_and_manifest_reference_match(self) -> None:
        handle, declaration = next(iter(self.app["bundled_executas"].items()))
        tool_dir = (APP_ROOT / declaration["path"]).resolve()
        self.assertTrue(tool_dir.is_dir())
        self.assertEqual(handle, "study-coach")
        refs = [entry["tool_id"] for entry in self.manifest["required_executas"]]
        self.assertIn(f"bundled:{handle}", refs)
        self.assertEqual(self.executa["slug"], handle)

    def test_local_tool_id_matches_python_console_script(self) -> None:
        tool_id = self.executa["tool_id"]
        scripts = self.pyproject["project"]["scripts"]
        self.assertIn(tool_id, scripts)
        self.assertEqual(scripts[tool_id], "study_coach_plugin:main")

    def test_frontend_loads_generated_tool_map_before_module(self) -> None:
        self.assertLess(
            self.html.index('src="anna-tool-ids.js"'),
            self.html.index('src="app.js"'),
        )
        self.assertIn("window.__ANNA_TOOL_IDS__", self.javascript)
        self.assertIn('"study-coach"', self.javascript)
        self.assertIn('"tool-dev-ai-study-coach"', self.javascript)

    def test_invoked_method_is_declared_by_executa(self) -> None:
        self.assertIn('method: "study_coach"', self.javascript)
        self.assertIn('"name": "study_coach"', self.plugin)
        self.assertIn('if tool != "study_coach"', self.plugin)

    def test_sampling_is_declared_and_storage_permissions_are_minimal(self) -> None:
        self.assertIn('"host_capabilities": ["llm.sample"]', self.plugin)
        host_api = self.manifest["ui"]["host_api"]
        self.assertEqual(host_api["storage"], ["get", "set"])
        self.assertEqual(host_api["window"], ["set_title"])
        # Anna's current LLM runtime checks the app-level llm.complete grant
        # in addition to the Executa's llm.sample capability.
        self.assertEqual(host_api["llm"], ["complete"])
        self.assertNotIn("tools", host_api)
        self.assertEqual(host_api["llm"], ["complete"])


    def test_form_selects_have_native_options_and_compact_styles(self) -> None:
        for control_id in (
            "plan-level",
            "plan-weeks",
            "plan-hours",
            "quiz-difficulty",
            "quiz-count",
        ):
            self.assertIn(f'id="{control_id}"', self.html)
        self.assertIn("appearance: none", self.css)
        self.assertIn("cursor: pointer", self.css)
        self.assertIn("overflow-y: hidden", self.css)
        self.assertIn("@media (max-width: 760px)", self.css)


    def test_local_file_drop_zone_supports_source_project_document_types(self) -> None:
        self.assertIn('id="file-drop-zone"', self.html)
        self.assertIn('id="file-input"', self.html)
        self.assertIn('id="choose-files-btn"', self.html)
        self.assertIn('id="use-for-quiz-btn"', self.html)
        for extension in ("pdf", "docx", "txt", "md", "csv", "json"):
            self.assertIn(f'"{extension}"', self.javascript)
        self.assertIn("extractPdfText(file)", self.javascript)
        self.assertIn("mammoth.extractRawText", self.javascript)
        self.assertIn("MAX_FILE_BYTES = 10 * 1024 * 1024", self.javascript)
        self.assertIn("MAX_MATERIAL_CHARS = 30000", self.javascript)

    def test_pinned_document_parsers_have_explicit_csp_and_external_origin(self) -> None:
        bundle = self.manifest["ui"]["bundle"]
        self.assertIn("https://cdn.jsdelivr.net", bundle["external_origins"])
        csp = self.manifest["ui"]["csp_overrides"]
        self.assertIn("https://cdn.jsdelivr.net", csp["script-src"])
        self.assertIn("blob:", csp["worker-src"])
        self.assertIn("pdfjs-dist@6.4.299", self.javascript)
        self.assertIn("mammoth@1.13.0", self.javascript)

    def test_document_text_is_loaded_before_only_explicit_ai_actions(self) -> None:
        self.assertIn("Files are extracted in your browser", self.html)
        self.assertIn("text is sent to Anna only when you request an AI action", self.html)
        self.assertIn('id="summarize-btn"', self.html)
        self.assertIn('id="answer-btn"', self.html)
        self.assertIn('id="use-for-quiz-btn"', self.html)

    def test_frontend_displays_runtime_errors_and_loading_status(self) -> None:
        self.assertIn("Working with Anna's model", self.javascript)
        self.assertIn("setStatus(statusElement, getErrorMessage(error), \"error\")", self.javascript)
        self.assertIn('role="status"', self.html)

    def test_frontend_does_not_require_a_provider_api_key(self) -> None:
        self.assertNotIn("GOOGLE_API_KEY", self.javascript)
        self.assertNotIn("google-genai", self.javascript)
        self.assertIn("anna.tools.invoke", self.javascript)


if __name__ == "__main__":
    unittest.main()
