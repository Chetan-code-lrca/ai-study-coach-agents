# AI Study Coach — Anna App

This is the Anna-native version of the existing AI Study Coach project. The original Streamlit app remains at the repository root and is not replaced by this app.

## Features

- Generate a multi-week study plan from subject, level, available daily time, and learning goals.
- Drag and drop or browse for PDF, DOCX, TXT, Markdown, CSV, and JSON study files.
- Extract document text in the browser, review/edit it, and ask Anna to summarize it, explain concepts, or answer questions grounded in the source.
- Generate multiple-choice quizzes from a topic or from the loaded study material.
- Score quiz attempts, show answer explanations, and save study-plan/quiz activity with Anna Storage.
- Render model answers as formatted Markdown, including inline and display LaTeX equations with locally bundled KaTeX.

## Architecture

The app calls Anna's documented frontend Host API, `anna.llm.complete(...)`, directly from the UI. This avoids sending Unicode-rich document text through a Windows Python Executa subprocess, which caused character-encoding errors. The app needs the manifest grant `ui.host_api.llm: ["complete"]`; it does not require a separate Gemini API key or a bundled Executa.

The app follows the official [Anna LLM demo](https://github.com/whtcjdtc2007/anna-executa-examples/tree/6325e4c44f9a43d756a40eb20df32918610483bb/examples/anna-app-llm-demo) and [Build on Anna 101](https://forum.anna.partners/t/build-on-anna-101/228) direct-call pattern.

## Requirements

- Node.js 22 or newer
- Anna CLI (`npm install -g @anna-ai/cli`)
- `uv` for the Anna local harness
- An Anna account with developer access activated and CLI login completed

## Run locally

From the repository root, use PowerShell:

    cd anna-app
    npm install
    npm run build
    npm test
    python -m unittest discover -s tests -v
    anna-app validate --strict
    anna-app dev --port 5181

Open the local URL printed by the CLI. Keep the terminal running while testing.

## Local document handling

- File text extraction runs in the browser using locally bundled, version-pinned PDF.js and Mammoth.
- File bytes are not uploaded for extraction. Extracted text is sent to Anna only when an AI action is requested.
- Maximum file size: 10 MB per file. Maximum combined study material: 30,000 characters.
- Scanned/image-only PDFs are not supported because OCR is not included.
- An internet connection is needed during `npm install`; PDF/DOCX parsing and equation rendering after the build use locally bundled assets and do not require a third-party CDN.

## Automated checks and limits

GitHub Actions builds the self-contained frontend bundle (including PDF.js worker and KaTeX stylesheet/fonts), runs prompt/Markdown/math tests, verifies Anna manifest and frontend contracts, checks JavaScript syntax, and runs the existing Streamlit regression workflow. These automated tests cannot replace a live request against your signed-in Anna account or testing with your own PDFs/DOCX files.
