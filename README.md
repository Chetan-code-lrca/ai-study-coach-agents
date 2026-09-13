# AI Study Coach

AI Study Coach is a Python/Streamlit app for building study plans, working with study material, generating quizzes, and keeping a simple record of study activity.

The repository also contains older agent and service code from earlier versions of the project. The Streamlit app at the root is the maintained entry point for running the current application.

## Current app

Run:

```bash
streamlit run streamlit_app.py
```

`streamlit_app.py` starts `src/frontend/app.py`.

The current Streamlit app has these sections:

- **Study Plan** — creates a multi-week plan from a subject, level, available time, and goals.
- **Document Learning** — reads TXT, PDF, DOCX, CSV, and JSON material and can summarize it, explain concepts, or answer questions about it.
- **Quiz Generator** — creates multiple-choice quizzes and shows the score and explanations after submission.
- **Progress** — records generated plans and completed quizzes for the current Streamlit session.
- **Profile** — keeps a small student profile in the current session.

## Requirements

- Python 3.11 or newer
- pip
- A Google Gemini API key for the AI features

## Run locally

### 1. Clone the repository

```bash
git clone https://github.com/Chetan-code-lrca/ai-study-coach-agents.git
cd ai-study-coach-agents
```

### 2. Create a virtual environment

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

### 3. Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The main application uses Streamlit, Google's `google-genai` SDK, `pypdf`, and `python-docx`. The repository also keeps dependencies used by the older agent/service modules. fileciteturn767file0

### 4. Add your Gemini API key

Linux/macOS:

```bash
export GOOGLE_API_KEY="your-gemini-api-key"
```

Windows PowerShell:

```powershell
$env:GOOGLE_API_KEY = "your-gemini-api-key"
```

Never commit the real key to Git.

### 5. Start Streamlit

```bash
streamlit run streamlit_app.py
```

Streamlit will print the local address, normally:

```text
http://localhost:8501
```

## Streamlit Community Cloud

Use the following application settings:

```text
Repository: Chetan-code-lrca/ai-study-coach-agents
Branch: main
Main file: streamlit_app.py
```

Add this to the app secrets:

```toml
GOOGLE_API_KEY = "your-gemini-api-key"
```

The application reads the key from Streamlit secrets first and then from the environment. fileciteturn760file0

## How the AI side works

The maintained frontend uses Gemini through Google's `google-genai` client. The current model name in the application is `gemini-3.8-flash`. fileciteturn760file0

The application sends a prompt when a user asks for a study plan, summary, concept explanation, question answer, or quiz. Uploaded documents are converted to text locally before that text is included in an AI request. PDF files are read with `pypdf`, and DOCX files with `python-docx`. fileciteturn760file0

## Data handling

The maintained frontend keeps study history, quiz history, the active quiz, document text, and the profile in Streamlit session state. That data is not backed by a database in the current frontend. fileciteturn760file0

The repository also contains an older `src/main.py` implementation with a local `.study_coach_data` directory and older Gemini/agent code. That code is kept as part of the project history and experimentation; it is not the entry point used by `streamlit_app.py`. fileciteturn744file0

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

## Checking the app

The basic syntax check is:

```bash
python -m py_compile streamlit_app.py src/frontend/app.py
```

The main application entry point is deliberately small: it loads the maintained Streamlit frontend with `runpy`. fileciteturn736file0

## Notes about the older agent code

The repository still contains an earlier `StudyPlannerAgent` implementation and a separate Gemini service. Those modules use the older `google.generativeai` package and different model names from the maintained frontend. They are useful as development/experimental code, but they are not required to run the current Streamlit app. fileciteturn748file0 fileciteturn755file0

## Current limitations

- study history and profile data are session-based in the maintained frontend;
- there is no account system or cross-device sync;
- uploaded documents are processed as text rather than stored in a document database;
- Gemini usage requires a valid API key and is subject to the provider's availability and limits;
- the older agent/service layer is separate from the maintained Streamlit frontend.

## License

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0).
