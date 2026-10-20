# AI Study Coach — Anna App

This is the Anna-native version of the existing AI Study Coach project. The original Streamlit app remains at the repository root and is not replaced by this migration.

## Features in this first version

- Generate a multi-week study plan from subject, level, available daily time, and learning goals.
- Summarize pasted notes, explain key concepts, and answer questions using the supplied material as the source.
- Generate multiple-choice quizzes, score attempts, and show answer explanations.
- Save study-plan and quiz activity with Anna Storage.
- Use Anna's hosted LLM through the bundled Python Executa and reverse Sampling; this app does not require a separate Gemini API key.

## Requirements

- Node.js 22 or newer
- uv
- Anna CLI, installed with npm install -g @anna-ai/cli
- An Anna account with developer access activated and CLI login completed
- The app-level `ui.host_api.llm: ["complete"]` permission declared in `manifest.json` and the Executa's `host_capabilities: ["llm.sample"]` permission

## Run locally

From the repository root, run the following PowerShell commands:

    cd anna-app
    anna-app validate --strict
    anna-app dev

Open the local URL printed by the CLI (usually http://localhost:5180/) and test the Study plan, Learn from notes, Practice quiz, and Progress tabs.

If an LLM request reports a manifest permission error, confirm `ui.host_api.llm` includes `complete` and rerun `anna-app validate --strict`. Reverse sampling also requires the bundled Executa to declare `host_capabilities: ["llm.sample"]` and the user's Executa sampling grant to be enabled in Anna. The [official Anna LLM demo manifest](https://github.com/whtcjdtc2007/anna-executa-examples/blob/6325e4c44f9a43d756a40eb20df32918610483bb/examples/anna-app-llm-demo/manifest.json) shows the host LLM grant alongside a bundled sampling Executa. The GitHub tests exercise the reverse-sampling protocol offline; they do not require developer credentials or prove that the user's live sampling grant is enabled.

## Automated checks

Run from the repository root:

    python -m unittest discover -s anna-app/tests -v
    anna-app validate --strict

The GitHub Actions workflow runs strict Anna validation and offline unit/contract tests for pull requests that change this directory.

## Notes and limitations

- The Anna app initially accepts pasted text; it does not yet provide the Streamlit version's PDF/DOCX file-upload flow.
- Study plans and completed quiz attempts are stored in Anna Storage. This first version does not include a separate sign-in flow or profile editor.
- The tests verify prompt validation, configuration wiring, and frontend/Executa contracts. They do not prove live LLM availability, sampling grants, production publishing, or user adoption.
