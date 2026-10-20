# AI Study Coach — Anna App

This is the Anna-native version of the existing AI Study Coach project. The original Streamlit app remains at the repository root and is not replaced by this migration.

## Features in this first version

- Generate a multi-week study plan from subject, level, available daily time, and learning goals.
- Drag and drop or browse for PDF, DOCX, TXT, Markdown, CSV, and JSON study files; extract text in the browser and review/edit it before AI use.
- Summarize notes, explain key concepts, and answer questions using the supplied material as the source.
- Copy loaded study material into the quiz source field to generate a quiz from your own files.
- Generate multiple-choice quizzes, score attempts, and show answer explanations.
- Save study-plan and quiz activity with Anna Storage.
- Use Anna's hosted LLM through the bundled Python Executa and reverse Sampling; this app does not require a separate Gemini API key.

## Requirements

- Node.js 22 or newer
- uv
- Anna CLI, installed with npm install -g @anna-ai/cli
- An Anna account with developer access activated and CLI login completed
- Node/npm to build the local browser bundle containing the pinned PDF.js and Mammoth parsers
- The app-level `ui.host_api.llm: ["complete"]` permission declared in `manifest.json` and the Executa's `host_capabilities: ["llm.sample"]` permission

## Run locally

From the repository root, run the following PowerShell commands:

    cd anna-app
    npm install
    npm run build
    anna-app validate --strict
    anna-app dev --port 5181

Open the local URL printed by the CLI (usually http://localhost:5180/) and test the Study plan, Learn from notes, Practice quiz, and Progress tabs.

If an LLM request reports a manifest permission error, confirm `ui.host_api.llm` includes `complete` and rerun `anna-app validate --strict`. Reverse sampling also requires the bundled Executa to declare `host_capabilities: ["llm.sample"]` and the user's Executa sampling grant to be enabled in Anna. The [official Anna LLM demo manifest](https://github.com/whtcjdtc2007/anna-executa-examples/blob/6325e4c44f9a43d756a40eb20df32918610483bb/examples/anna-app-llm-demo/manifest.json) shows the host LLM grant alongside a bundled sampling Executa. The GitHub tests exercise the reverse-sampling protocol offline; they do not require developer credentials or prove that the user's live sampling grant is enabled.

## Automated checks

Run from the repository root:

    cd anna-app
    npm install
    npm run build
    python -m unittest discover -s tests -v
    anna-app validate --strict

The GitHub Actions workflow runs strict Anna validation and offline unit/contract tests for pull requests that change this directory.

## Notes and limitations

- File text extraction is performed in the browser using locally bundled, version-pinned PDF.js and Mammoth. File bytes are not uploaded for extraction; extracted text is only sent to Anna when you click an AI action.
- Run `npm install` and `npm run build` after pulling changes and before `anna-app dev`. This generates `bundle/app.js` and the local PDF worker.
- The per-file size limit is 10 MB and the total extracted study-material limit is 30,000 characters. Scanned/image-only PDFs are not supported because OCR is not included.
- An internet connection is needed during the build to download the pinned npm dependencies. Parsing files after the build does not require a third-party CDN.
- Study plans and completed quiz attempts are stored in Anna Storage. This first version does not include a separate sign-in flow or profile editor.
- The tests verify prompt validation, configuration wiring, and frontend/Executa contracts. They do not prove live LLM availability, sampling grants, production publishing, or user adoption.
