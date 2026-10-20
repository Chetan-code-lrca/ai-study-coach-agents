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
- Anna's LLM sampling permission enabled for the Executa when prompted by the platform

## Run locally

From the repository root, run the following PowerShell commands:

    cd anna-app
    anna-app validate --strict
    anna-app dev

Open the local URL printed by the CLI (usually http://localhost:5180/) and test the Study plan, Learn from notes, Practice quiz, and Progress tabs.

If a request reports SAMPLING_NOT_GRANTED or SAMPLING_NOT_NEGOTIATED, check the app/Executa sampling grant in Anna and confirm that your account is permitted to use the host LLM. The GitHub tests intentionally do not call a live model or require developer credentials.

## Automated checks

Run from the repository root:

    python -m unittest discover -s anna-app/tests -v
    anna-app validate --strict

The GitHub Actions workflow runs strict Anna validation and offline unit/contract tests for pull requests that change this directory.

## Notes and limitations

- The Anna app initially accepts pasted text; it does not yet provide the Streamlit version's PDF/DOCX file-upload flow.
- Study plans and completed quiz attempts are stored in Anna Storage. This first version does not include a separate sign-in flow or profile editor.
- The tests verify prompt validation, configuration wiring, and frontend/Executa contracts. They do not prove live LLM availability, sampling grants, production publishing, or user adoption.
