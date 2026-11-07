[![Streamlit Smoke Check](https://github.com/Chetan-code-lrca/ai-study-coach-agents/actions/workflows/streamlit-smoke.yml/badge.svg)](https://github.com/Chetan-code-lrca/ai-study-coach-agents/actions/workflows/streamlit-smoke.yml)

# AI Study Coach

AI Study Coach is a Python/Streamlit app for building study plans, working with study material, generating quizzes, and keeping a simple record of study activity.

The repository also contains older agent and service code from earlier versions of the project. The current Streamlit app is started from `streamlit_app.py`; it remains a separate implementation from the key-free Vercel browser edition.

## Deployment architecture

This repository contains three related application surfaces:

- **Vercel browser app:** the public site lives at [ai-study-coach-agents.vercel.app](https://ai-study-coach-agents.vercel.app/). The **Launch the web app** links open the actual study workspace at `/app/`, built from the reviewed Anna UI. The browser edition uses localStorage for profile, notes, plans, and quiz history; those records remain in that browser and do not sync automatically to Anna or other devices.
- **Vercel browser app:** study planning, note summaries, concept explanations, note-grounded answers, and quizzes use built-in rule-based/extractive tools in the browser. The browser edition does not call `/api/study`, send prompts to external model providers, or require an AI API key. It is reliable and key-free, but less flexible than a hosted language model. Profile, notes, plans, and quiz history stay in that browser's local storage and do not automatically sync to Anna or other devices.
- **Anna-native app:** `anna-app/` is the separate Anna-runtime edition. It uses Anna's LLM and Storage host APIs and does not need a Vercel AI API key.
- **Streamlit edition:** `streamlit_app.py` remains an alternative Python-hosted implementation for Streamlit Community Cloud. Set `OPENROUTER_API_KEY` in that service's secrets. Its session state is independent of both the Vercel browser app and the Anna-native app.

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
- An OpenRouter API key (`OPENROUTER_API_KEY`) for the maintained Streamlit AI features. The browser edition does not need an API key.

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

Set the OpenRouter API key before starting the app.

Linux/macOS:

```bash
export OPENROUTER_API_KEY="your-openrouter-api-key"
```

Windows PowerShell:

```powershell
$env:OPENROUTER_API_KEY = "your-openrouter-api-key"
```

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

Do not put the real key in the repository.

## Streamlit AI integration

The maintained Streamlit frontend sends prompts to the OpenRouter chat-completions API using `OPENROUTER_API_KEY`. The configured model route is `openrouter/free`; the upstream model selected by that route and its availability can change. The compatibility function is still named `gemini_text`, but it does not call Google Gemini.

Study-plan generation, document summaries and explanations, document Q&A, and quiz generation use this provider. PDF and DOCX files are converted to text locally with `pypdf` and `python-docx` before the extracted text is sent in an AI request. Do not upload confidential material unless you are authorised to share it with the configured provider.

## Data handling

The maintained frontend keeps the active profile, study-plan history, quiz history, current quiz, answers, and document text in Streamlit session state. If `AZURE_STORAGE_ACCOUNT_URL` is configured, it additionally persists the profile, study-plan history, and quiz history to the `studycoach-data` Azure Blob container using `DefaultAzureCredential`; without that setting, no Azure Blob persistence is attempted. Document text, the current quiz, and in-progress answers are not included in the persisted blob payload.

The optional persistence uses a generated 32-character `sid` in the Streamlit page URL as a per-browser-session identifier. It is not an authenticated account system: treat URLs containing `sid` as private and do not share them. Anyone who obtains a valid session URL may be able to access that session's persisted study history/profile through the app. The Streamlit app has no user sign-in or account recovery.

The repository also contains an older `src/main.py` implementation with its own local `.study_coach_data` directory and older Gemini/agent code. That version is separate from the current `streamlit_app.py` path.

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
│   └── main.py
├── .devcontainer/
├── requirements.txt
├── LICENSE
└── README.md
```

`streamlit_app.py` loads `src/frontend/app.py`, which contains the maintained Streamlit interface.

## Quick checks

To check that the two main Python entry files compile:

```bash
python -m py_compile streamlit_app.py src/frontend/app.py
```

## Older agent code

The `src/agents/` and `src/services/` modules are earlier parts of the project. They include separate Gemini integrations such as the older study planner and Gemini service. They are useful for development and experimentation, but they are not needed to start the current Streamlit app.

## Current limitations

- the Vercel browser edition keeps its data in browser localStorage; the Streamlit edition keeps active state in Streamlit session state and can optionally persist profile/study/quiz history to Azure Blob Storage;
- there is no account system or cloud synchronization;
- uploaded documents are processed as text rather than stored in a document database;
- the Vercel browser app runs key-free offline study tools; generated content is extractive or rule-based rather than full LLM output;
- the maintained Streamlit edition uses OpenRouter and requires `OPENROUTER_API_KEY`; older agent/service modules may use Google Gemini and require `GOOGLE_API_KEY`;
- the older agent/service modules use a different implementation from the maintained Streamlit frontend.

## License

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
