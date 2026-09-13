# AI Study Coach

AI Study Coach is a Python/Streamlit app for building study plans, working with study material, generating quizzes, and keeping a simple record of study activity.

The repository also contains older agent and service code from earlier versions of the project. The current Streamlit app is started from `streamlit_app.py`.

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
- A Google Gemini API key for the AI features

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

Set the Gemini API key before starting the app.

Linux/macOS:

```bash
export GOOGLE_API_KEY="your-gemini-api-key"
```

Windows PowerShell:

```powershell
$env:GOOGLE_API_KEY = "your-gemini-api-key"
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

Add the Gemini key to the app secrets:

```toml
GOOGLE_API_KEY = "your-gemini-api-key"
```

Do not put the real key in the repository.

## Gemini integration

The maintained Streamlit frontend uses Google's `google-genai` Python SDK and the model configured as `gemini-3.8-flash`.

The Gemini call is used for study-plan generation, document summaries and explanations, document Q&A, and quiz generation. PDF and DOCX files are converted to text locally with `pypdf` and `python-docx` before an AI request is made.

## Data handling

The maintained frontend stores the active profile, study-plan history, quiz history, current quiz, answers, and document text in Streamlit session state. There is no database or cross-device account system in this version.

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

- profile, plan history, quiz history, and document text are session-based;
- there is no account system or cloud synchronization;
- uploaded documents are processed as text rather than stored in a document database;
- Gemini features require a valid Google API key;
- the older agent/service modules use a different implementation from the maintained Streamlit frontend.

## License

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
