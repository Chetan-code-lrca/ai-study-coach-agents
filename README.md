# AI Study Coach

AI Study Coach is a Python/Streamlit learning platform for personalized study plans, document learning, AI-generated quizzes, progress tracking, and resource discovery.

## Production Streamlit app

The production-facing Streamlit entrypoint is:

```text
streamlit_app.py
```

It launches the maintained frontend at `src/frontend/app.py`.

### Local run

```bash
git clone https://github.com/Chetan-code-lrca/ai-study-coach-agents.git
cd ai-study-coach-agents
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

Windows PowerShell:

```powershell
py -3.11 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
streamlit run streamlit_app.py
```

## Gemini configuration

The app uses Google's current `google-genai` Python SDK and the stable `gemini-3.8-flash` model.

For local development:

```bash
export GOOGLE_API_KEY="your-gemini-api-key"
```

PowerShell:

```powershell
$env:GOOGLE_API_KEY = "your-gemini-api-key"
```

For Streamlit Community Cloud, add the same secret in the app's **Settings → Secrets**:

```toml
GOOGLE_API_KEY = "your-gemini-api-key"
```

The application does not store the API key in the repository.

## Deploy on Streamlit Community Cloud

1. Open Streamlit Community Cloud and sign in with GitHub.
2. Create a new app from `Chetan-code-lrca/ai-study-coach-agents` and branch `main`.
3. Set the main file path to `streamlit_app.py`.
4. Add `GOOGLE_API_KEY` under the app secrets.
5. Deploy.

After deployment, pushes to `main` can be configured to trigger Streamlit Cloud redeploys automatically.

### Important

This repository is a **Streamlit/Python application**. It is not a Vite/Node application and should not be deployed as a Vercel Vite project. The previous Vercel setup tried to run `npm run build` and failed because this project has no `package.json` build entrypoint.

## Features

### Study Plan
Generate a structured multi-week study plan based on subject, level, available time, and learning goals.

### Document Learning
Upload TXT, PDF, DOCX, CSV, or JSON study material, then summarize it, explain key concepts, or ask questions about it.

### Quiz Generator
Generate multiple-choice quizzes with answer keys and explanations. Quiz scores are recorded in the current Streamlit session.

### Progress
Track generated study plans, completed quizzes, and average quiz performance during the current session.

### Profile
Maintain a lightweight in-session student profile for personalization.

## Repository structure

```text
ai-study-coach-agents/
├── streamlit_app.py
├── .streamlit/config.toml
├── src/
│   ├── main.py
│   ├── agents/
│   ├── services/
│   └── frontend/app.py
├── .devcontainer/
├── requirements.txt
├── LICENSE
└── README.md
```

The older `src/main.py` and service/agent modules remain in the repository for development and experimentation. The production Streamlit deployment uses the maintained `streamlit_app.py` entrypoint.

## Testing

The repository includes a GitHub Actions smoke check that installs the deployment dependencies and compiles the Streamlit entrypoint:

```bash
python -m py_compile streamlit_app.py src/frontend/app.py
```

Run it locally with:

```bash
python -m py_compile streamlit_app.py src/frontend/app.py
```

## Development status

The Streamlit frontend is a deployable prototype. Persistent cross-user profile/history storage and the Firebase data layer are not part of the current deployment architecture.

## License

Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0). See `LICENSE` for the full terms.

## Author

Chetan Inaganti
