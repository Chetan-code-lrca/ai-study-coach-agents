[![Streamlit Smoke Check](https://github.com/Chetan-code-lrca/ai-study-coach-agents/actions/workflows/streamlit-smoke.yml/badge.svg)](https://github.com/Chetan-code-lrca/ai-study-coach-agents/actions/workflows/streamlit-smoke.yml)

# AI Study Coach

AI Study Coach is a Python/Streamlit app for building study plans, working with study material, generating quizzes, and keeping a simple record of study activity.

The repository also contains older agent and service code from earlier versions of the project. The current Streamlit app is started from `streamlit_app.py`; it remains a separate implementation from the key-free Vercel browser edition.

## Deployment architecture

This repository contains three related application surfaces:

- **Vercel browser app:** the public site lives at https://ai-study-coach-agents.vercel.app/. Its /app/ workspace is built from the reviewed Anna UI and runs local rule-based/extractive study tools. It does not call /api/study, require a model API key, or sync its localStorage data to the Streamlit or Anna editions.
- **Anna-native app:** anna-app/ is the separate Anna-runtime edition. It uses Anna's LLM and Storage host APIs.
- **Streamlit edition:** streamlit_app.py is the server-hosted AI implementation. Its current AI calls go to OpenRouter using OPENROUTER_API_KEY and the openrouter/free model alias. It is separate from the Vercel browser and Anna-native editions.

Vercel serves the static landing page and browser app. The retired `/api/study` endpoint returns `410 Gone`; the browser edition has no external AI proxy. Vercel does not run a persistent Streamlit server.


## Sync and update the Anna-native app on Windows

From a clean local clone of this repository, run one of these from the repository root.

**Windows PowerShell**

    .\scripts\Update-AnnaApp.ps1

**Linux / WSL / macOS**

    bash scripts/update-anna-app.sh

These scripts check for uncommitted changes, fast-forward the local main branch from GitHub, rebuild the Anna frontend, run tests, validate the manifest and Host API permissions, and check generated JavaScript syntax. They do not discard local edits.

After local checks pass, authenticate with Anna if needed and push the verified bundle as a working draft.

PowerShell:

    anna-app login --host https://anna.partners
    .\scripts\Update-AnnaApp.ps1 -PushToAnna

Linux / WSL / macOS:

    anna-app login --host https://anna.partners
    bash scripts/update-anna-app.sh --push-to-anna

The latest version shown in Anna Developer Console was **0.1.3**, cut before the latest duplicate-note handling change. A successful `anna-app apps push` updates the working draft; it does not itself publish a release. Run the local checks and push the working draft, install and test it in Anna (including note deduplication, source-linked plans/quizzes, and persistence), then cut **0.1.4** and submit that new cut for review. Do not submit/publish the older `0.1.3` snapshot if you want to include the latest code. The Vercel-only full-width dashboard styling is built for the browser deployment and is not part of the Anna-native UI bundle.




## What the current app does

### Study Plan

Generate a multi-week study plan from a subject, current level, available study time, and learning goals.

### Document Learning

Upload or paste study material in TXT, PDF, DOCX, CSV, or JSON form. The app can summarize the material, explain key concepts, and answer questions about it.

### Quiz Generator

Generate multiple-choice quizzes with answer keys and explanations. Scores are recorded during the current Streamlit session.

### Progress

See generated study plans, completed quizzes, and the average quiz score for the current session.

### Profile

Save a small student profile for the current session.

## Requirements

- Python 3.11 or newer
- pip
- An OpenRouter API key for Streamlit AI features
- Optional Azure Blob Storage account access for persistent progress

## Run locally

Clone the repository:

```bash
git clone https://github.com/Chetan-code-lrca/ai-study-coach-agents.git
cd ai-study-coach-agents
```

Create and activate a virtual environment.

Linux/macOS:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

Install the dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Copy the environment template and set the OpenRouter key.

Linux/macOS:

```bash
cp .env.example .env
# Edit .env and set OPENROUTER_API_KEY
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
# Edit .env and set OPENROUTER_API_KEY
```

The app loads .env for local runs. In hosted environments, configure OPENROUTER_API_KEY as a secret or environment variable. Do not commit real credentials.

Start Streamlit:

```bash
streamlit run streamlit_app.py
```

Open the local address shown by Streamlit, normally `http://localhost:8501`.

## Streamlit Community Cloud

Create a Streamlit app from this repository with:

```text
Repository: Chetan-code-lrca/ai-study-coach-agents
Branch: main
Main file: streamlit_app.py
```

Add the OpenRouter key to the app secrets:

```toml
OPENROUTER_API_KEY = "your-openrouter-api-key"
```

Do not put the real key in the repository. For optional progress persistence, configure AZURE_STORAGE_ACCOUNT_URL and the app's managed identity with access to the studycoach-data blob container.

## OpenRouter integration

The maintained Streamlit frontend sends AI requests to https://openrouter.ai/api/v1/chat/completions using the openrouter/free model alias. Study-plan prompts, quiz prompts, questions, and source text selected for document or quiz actions are sent to OpenRouter. Review the provider's current privacy and retention terms before using the service with sensitive material.

PDF and DOCX files are converted to text locally first. Uploaded files are limited to 10 MiB, PDF files to 100 pages, and extracted document text to 50,000 characters. The app only sends document text when an AI action is requested. These limits reduce oversized processing; they do not make confidential data safe to share.

## Data handling and persistence

The Streamlit app keeps the active quiz, answers, document text, and current interaction state in Streamlit session state. When AZURE_STORAGE_ACCOUNT_URL is configured and the app identity can access the private studycoach-data container, it also stores study history, quiz history, and the profile in Azure Blob Storage. Without that configuration, progress is session-only.

Persistent records are keyed by a 32-character session ID in the sid query parameter. Treat the complete app URL as private: someone who obtains the same session link may be able to access the associated saved progress while storage is enabled. This is not a user-account or role-based access system. Configure a retention and deletion policy for the storage container before using it with an organization.

The repository also contains older agent/service code, including Gemini integrations. Those modules are separate from the maintained streamlit_app.py path.

## Project structure

```text
ai-study-coach-agents/
├── streamlit_app.py
├── .streamlit/
│   └── config.toml
├── src/
│   ├── frontend/
│   │   └── app.py
│   ├── agents/
│   ├── services/
│   │   └── document_ingestion.py  # bounded document text extraction
│   └── main.py
├── .devcontainer/
├── requirements.txt
├── LICENSE
└── README.md
```

`streamlit_app.py` loads `src/frontend/app.py`, which contains the maintained Streamlit interface.

## Quick checks

Run the tests and compile the active entry points:

```bash
python -m pytest tests/ -q
python -m py_compile streamlit_app.py src/frontend/app.py src/services/document_ingestion.py
```

## Older agent code

The `src/agents/` and `src/services/` modules are earlier parts of the project. They include separate Gemini integrations such as the older study planner and Gemini service. They are useful for development and experimentation, but they are not needed to start the current Streamlit app.

## Current limitations

- there is no user account system, role-based access control, or organization/tenant isolation;
- optional Azure Blob progress records are keyed by a private session URL rather than an authenticated user identity;
- document extraction is text-oriented and may not preserve diagrams, tables, equations, or complex layouts;
- AI output can be incorrect and requires verification against course material;
- the Vercel browser app uses extractive/rule-based tools, not a hosted LLM;
- the Streamlit edition depends on OpenRouter availability, model routing, and the configured API key;
- the older agent/service modules are not the active Streamlit implementation.

## License

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
