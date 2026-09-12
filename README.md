# AI Study Coach

AI Study Coach is a Python/Streamlit project for study planning, document-based learning, quizzes, progress tracking, and resource recommendations.

The repository contains several agent-style modules around Google Gemini, along with a Streamlit interface. It also contains local fallbacks and prototype service code, so not every component in the repository is wired into the main screen yet.

## What is in the repository

The code is split into a few parts:

```text
ai-study-coach-agents/
├── src/
│   ├── main.py                    # Main Streamlit learning app
│   ├── agents/
│   │   ├── data_processing.py
│   │   ├── progress_tracker.py
│   │   ├── quiz_generator.py
│   │   ├── resource_recommender.py
│   │   ├── study_planner.py
│   │   └── user_interaction.py
│   ├── services/
│   │   ├── error_handler.py
│   │   ├── firebase_service.py
│   │   └── gemini_service.py
│   └── frontend/
│       └── app.py                 # Separate Streamlit UI with Gemini quiz features
├── .devcontainer/
│   └── devcontainer.json          # VS Code / GitHub Codespaces setup
├── .env.example
├── requirements.txt
├── LICENSE
└── README.md
```

## What you can run today

There are two Streamlit entry points in the repository.

### `src/main.py`

This is the simpler all-in-one learning interface. It has tabs for:

- Study sessions
- Document summaries
- Flashcard generation
- Question answering from pasted text
- User profile data
- Local work-session history

It reads `GOOGLE_API_KEY` from the environment when Gemini features are used. It also writes local files under `.study_coach_data/` for the profile and work-session history.

### `src/frontend/app.py`

This is a more presentation-oriented Streamlit interface. The repository's dev-container configuration starts this file automatically on port `8501`.

Use whichever interface matches what you are working on. The two files are separate applications; changing one does not automatically change the other.

## Requirements

Recommended for local development:

- Python 3.10 or newer
- Git
- A Google Gemini API key for live generation features

The checked-in development container uses Python 3.11, which is a good reference environment for this repository.

## 1. Clone

```bash
git clone https://github.com/Chetan-code-lrca/ai-study-coach-agents.git
cd ai-study-coach-agents
```

## 2. Create a virtual environment

### Linux / macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
```

Then upgrade pip:

```bash
python -m pip install --upgrade pip
```

## 3. Install the dependencies

```bash
python -m pip install -r requirements.txt
```

The current requirements file includes Streamlit, Google Gemini support, Firebase packages, PDF/document processing, HTTP clients, testing tools, and logging utilities.

One detail worth knowing: `src/services/gemini_service.py` imports `tenacity`, but `tenacity` is not currently listed in `requirements.txt`. If you use that service module directly, install it as well:

```bash
python -m pip install tenacity
```

## 4. Configure Gemini

Create a local `.env` file from the example:

### Linux / macOS

```bash
cp .env.example .env
```

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

At minimum, set:

```env
GOOGLE_API_KEY=your_gemini_api_key
```

The current `src/main.py` reads `GOOGLE_API_KEY` directly from the process environment, so your shell must have the variable available when Streamlit starts. The `.env` file is useful as a template, but `src/main.py` does not itself call `load_dotenv()` before reading the key.

For example, on Linux/macOS:

```bash
export GOOGLE_API_KEY="your_gemini_api_key"
```

On PowerShell:

```powershell
$env:GOOGLE_API_KEY = "your_gemini_api_key"
```

Do not commit a real `.env` file or service-account credentials.

## 5. Run the main app

From the repository root:

```bash
streamlit run src/main.py
```

Open the URL printed by Streamlit, normally:

```text
http://localhost:8501
```

## 6. Run the frontend app

The second UI can be started with:

```bash
streamlit run src/frontend/app.py
```

It also normally uses port `8501`.

## 7. Using the agent modules directly

The `src/agents/` directory contains individual components for different parts of the workflow.

### Study planner

`StudyPlannerAgent` accepts a student profile and asks Gemini for a seven-day study plan. It also contains a rule-based fallback when Gemini fails.

The module can be run directly after setting `GEMINI_API_KEY`:

```bash
python src/agents/study_planner.py
```

### Quiz generator

`QuizGeneratorAgent` is intended to generate multiple-choice questions from study material. The current PDF extraction method in the module is still a prototype and returns sample content rather than performing a full PDF extraction pipeline.

So the file is useful as an agent implementation example, but it should not be described as a finished PDF-to-quiz system yet.

### Progress tracker

`progress_tracker.py` contains progress-analysis logic and a small executable test section.

### Resource recommender

`resource_recommender.py` contains resource-search/recommendation logic and its own example/test flow.

### User interaction

`user_interaction.py` classifies simple user requests into categories such as help, quiz, and other study-related actions.

## How Gemini is used

Gemini is the language-model layer for several agents. The repository contains two styles of integration:

1. Some agents create a Gemini model directly with `google.generativeai`.
2. `src/services/gemini_service.py` provides a shared wrapper with retries, structured-output helpers, chat support, prompt-context handling, and a mock mode when no API key is available.

The shared service currently defaults to `gemini-2.0-flash-exp`, while some individual agents still use `gemini-1.5-pro` or `gemini-pro`. Those model names are part of the current source code; they are not a single project-wide model configuration.

## Firebase status

Firebase-related code exists in `src/services/firebase_service.py`, but the current implementation is partly a prototype. When Firebase credentials are not provided it uses in-memory storage; its production Firebase branches still contain placeholder `pass` sections.

The main Streamlit application in `src/main.py` uses local files for its profile and study history instead of requiring Firebase.

So you can run the main app without setting up Firebase.

## Local data

`src/main.py` creates:

```text
.study_coach_data/
├── user_profile.json
└── work_sessions.csv
```

These files hold the local profile and study-session information used by the app.

The application also writes logs under `logs/`.

## Dev Container / Codespaces

The repository includes `.devcontainer/devcontainer.json` with a Python 3.11 image and a post-attach command that starts:

```bash
streamlit run src/frontend/app.py --server.enableCORS false --server.enableXsrfProtection false
```

It forwards port `8501` and is set up for VS Code/GitHub Codespaces.

If you use Codespaces, this gives you a ready-made environment without having to install Python manually on your machine.

## Testing

The repository contains executable test/demo sections inside several agent and service files. Where pytest tests are present in your checkout, use:

```bash
python -m pytest
```

There is not currently a single, clearly separated end-to-end test suite covering every agent, service, and Streamlit screen.

## Troubleshooting

### Streamlit says the Gemini key is missing

Set `GOOGLE_API_KEY` in the environment before starting Streamlit:

```bash
export GOOGLE_API_KEY="your_gemini_api_key"
streamlit run src/main.py
```

### `ModuleNotFoundError: tenacity`

Install it explicitly:

```bash
python -m pip install tenacity
```

This is needed by `src/services/gemini_service.py` with the current dependency file.

### Firebase setup is blocking local development

You do not need Firebase to use `src/main.py`. Its profile and work-session data use local files.

### A claimed feature does not work end to end

Check whether the feature is connected to the Streamlit entry point you are running. The repository contains several prototype services and agent modules, and not all of them are used by both UIs.

## Development notes

This repository is best treated as a working prototype and learning project around multi-agent patterns, Gemini integration, Streamlit, and study tooling.

Some README claims from earlier versions of the project were stronger than the current source code supports, so the documentation above intentionally distinguishes working pieces from prototype or placeholder implementations.

## License

The repository is licensed under **Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)**. See `LICENSE` for the full text.

## Author

Chetan Inaganti
