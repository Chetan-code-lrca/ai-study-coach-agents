"""Stable Streamlit Cloud entrypoint for AI Study Coach."""

from pathlib import Path
import runpy


APP = Path(__file__).parent / "src" / "frontend" / "app.py"
runpy.run_path(str(APP), run_name="__main__")
