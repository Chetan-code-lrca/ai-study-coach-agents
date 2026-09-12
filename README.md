# AI Study Coach

AI Study Coach is a Python/Streamlit project for study planning, document-based learning, quizzes, progress tracking, and resource recommendations.

The repository contains several Gemini-based agent modules, a main Streamlit app, a second Streamlit frontend, local data storage, and Firebase service code.

## What is included

```text
ai-study-coach-agents/
├── src/
│   ├── main.py
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
│   └── frontend/app.py
├── .devcontainer/
├── .env.example
├── requirements.txt
├── LICENSE
└── README.md
```

## Run the main app

Requirements:

- Python 3.10+
- Git
- A Google Gemini API key for live generation

Clone and create a virtual environment:

```bash
git clone https://github.com/Chetan-code-lrca/ai-study-coach-agents.git
cd ai-study-coach-agents
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Set the Gemini key in the process environment:

```bash
export GOOGLE_API_KEY="your-gemini-api-key"
```

PowerShell:

```powershell
$env:GOOGLE_API_KEY = "your-gemini-api-key"
```

Start the main application:

```bash
streamlit run src/main.py
```

The app opens on `http://localhost:8501` by default.

## Second Streamlit interface

A separate UI is available at `src/frontend/app.py`:

```bash
streamlit run src/frontend/app.py
```

The two Streamlit applications are separate entry points. Features added to one are not automatically available in the other.

## Gemini integration

Gemini powers the language-generation parts of the project. `src/services/gemini_service.py` also provides retries, structured-output helpers, chat support, prompt context, and a mock mode.

Several older agent modules use their own Gemini model configuration, so model names are not uniform across the repository.

The shared service imports `tenacity`, so install it when working with that module:

```bash
python -m pip install tenacity
```

## Agent modules

`study_planner.py` generates seven-day study plans and has a rule-based fallback.

`quiz_generator.py` generates multiple-choice questions. Its current PDF extraction path is a prototype and uses sample content rather than a complete PDF ingestion pipeline.

`progress_tracker.py` contains progress-analysis logic.

`resource_recommender.py` contains study-resource recommendation logic.

`user_interaction.py` classifies simple study-related requests.

## Firebase

Firebase service code is included, but the main Streamlit application uses local files for its profile and work-session history. Firebase storage branches are not a complete production data layer yet.

The main app writes:

```text
.study_coach_data/
├── user_profile.json
└── work_sessions.csv
```

Logs are written under `logs/`.

## Codespaces / Dev Container

The repository includes a Python 3.11 development container configured to run `src/frontend/app.py` on port `8501`.

## Testing

Run the available Python tests with:

```bash
python -m pytest
```

The project does not currently have one end-to-end test suite covering every agent, service, and Streamlit screen.

## Development status

The project is a working prototype for multi-agent study tooling, Gemini integration, and Streamlit applications. Some agent and service modules are complete enough to run independently, while others are still being developed.

## License

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0). See `LICENSE` for the full terms.

## Author

Chetan Inaganti
