"""Production Streamlit frontend for AI Study Coach.

This file is intentionally self-contained so it can be deployed directly by
Streamlit Community Cloud without depending on the older prototype modules.
"""

from __future__ import annotations

import io
import json
import os
from datetime import datetime
from typing import Any

import streamlit as st
from google import genai
from google.genai import types
from pypdf import PdfReader
from docx import Document


APP_TITLE = "AI Study Coach"
MODEL_NAME = "gemini-3.8-flash"


st.set_page_config(
    page_title=APP_TITLE,
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)


def get_api_key() -> str:
    """Read the Gemini key from Streamlit secrets or the environment."""
    try:
        secret_value = st.secrets.get("GOOGLE_API_KEY", "")
    except Exception:
        secret_value = ""
    return str(secret_value or os.getenv("GOOGLE_API_KEY", "")).strip()


@st.cache_resource(show_spinner=False)
def get_client(api_key: str):
    """Create and cache the Gemini client for the current key."""
    return genai.Client(api_key=api_key)


def gemini_text(prompt: str, *, json_mode: bool = False) -> str:
    """Call Gemini with a production-safe error boundary."""
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "Google Gemini is not configured. Add GOOGLE_API_KEY to the "
            "Streamlit app secrets."
        )

    client = get_client(api_key)
    config = types.GenerateContentConfig(
        temperature=0.4,
        max_output_tokens=4096,
        response_mime_type="application/json" if json_mode else "text/plain",
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=config,
    )

    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Gemini returned an empty response.")
    return text


def extract_uploaded_text(uploaded_file) -> str:
    """Extract text from TXT, PDF, CSV, JSON, and DOCX study files."""
    suffix = uploaded_file.name.lower().rsplit(".", 1)[-1]
    data = uploaded_file.getvalue()

    if suffix in {"txt", "csv", "json"}:
        return data.decode("utf-8", errors="replace")

    if suffix == "pdf":
        reader = PdfReader(io.BytesIO(data))
        pages = [page.extract_text() or "" for page in reader.pages]
        return "\n\n".join(pages)

    if suffix == "docx":
        doc = Document(io.BytesIO(data))
        return "\n".join(paragraph.text for paragraph in doc.paragraphs)

    raise ValueError("Unsupported file type.")


def safe_json(text: str) -> dict[str, Any] | None:
    """Parse Gemini JSON responses even when fenced by markdown."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("\n", 1)[1] if "\n" in cleaned else cleaned
        cleaned = cleaned.rsplit("```", 1)[0]
    try:
        value = json.loads(cleaned)
        return value if isinstance(value, dict) else None
    except json.JSONDecodeError:
        return None


def init_state() -> None:
    defaults = {
        "study_history": [],
        "quiz_history": [],
        "quiz": None,
        "answers": {},
        "document_text": "",
        "profile": {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_header() -> None:
    st.markdown(
        "# 🎓 AI Study Coach\n"
        "Personalized study planning, document learning, quizzes, and progress tracking."
    )


def render_study_plan() -> None:
    st.header("📚 Study Plan")
    col1, col2 = st.columns(2)

    with col1:
        subject = st.selectbox(
            "Subject",
            ["Computer Science", "Mathematics", "Physics", "Chemistry", "Biology"],
        )
        level = st.select_slider(
            "Current level",
            options=["Beginner", "Intermediate", "Advanced"],
            value="Intermediate",
        )

    with col2:
        weeks = st.slider("Plan length (weeks)", 1, 12, 4)
        hours_per_day = st.slider("Study time per day (hours)", 0.5, 8.0, 2.0, 0.5)

    goals = st.text_area(
        "Learning goals",
        placeholder="Example: Prepare for semester exams, strengthen weak areas, and practice problem solving.",
    )

    if st.button("Generate AI Study Plan", type="primary", use_container_width=True):
        prompt = f"""
Create a practical study plan for a {level.lower()} student.
Subject: {subject}
Duration: {weeks} weeks
Available time: {hours_per_day} hours/day
Goals: {goals or 'Build strong conceptual understanding and problem-solving ability.'}

Return a day-by-day plan grouped by week. Include topic sequencing, practice,
revision, one weekly checkpoint, and realistic daily workload. Keep it concise.
"""
        try:
            with st.spinner("Building your study plan..."):
                plan = gemini_text(prompt)
            st.session_state.study_history.append(
                {
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "subject": subject,
                    "level": level,
                    "weeks": weeks,
                }
            )
            st.success("Study plan generated.")
            st.markdown(plan)
        except Exception as exc:
            st.error(str(exc))


def render_document_learning() -> None:
    st.header("📄 Document Learning")
    uploaded = st.file_uploader(
        "Upload study material",
        type=["txt", "pdf", "docx", "csv", "json"],
        help="The text is sent to Gemini only when you request an AI action.",
    )

    text = st.text_area(
        "Or paste study material",
        value=st.session_state.document_text,
        height=220,
    )

    if uploaded is not None:
        try:
            text = extract_uploaded_text(uploaded)
            st.session_state.document_text = text
            st.success(f"Loaded {uploaded.name} ({len(text):,} characters).")
        except Exception as exc:
            st.error(f"Could not read the file: {exc}")

    if not text.strip():
        st.info("Add some study material to enable summaries and Q&A.")
        return

    st.caption(f"Material size: {len(text):,} characters")

    a, b = st.columns(2)
    with a:
        if st.button("Summarize", use_container_width=True):
            try:
                with st.spinner("Summarizing..."):
                    result = gemini_text(
                        "Summarize the following study material. Provide a clear overview, "
                        "key concepts, important definitions, and a short revision checklist.\n\n"
                        + text[:50000]
                    )
                st.markdown(result)
            except Exception as exc:
                st.error(str(exc))

    with b:
        if st.button("Explain Key Concepts", use_container_width=True):
            try:
                with st.spinner("Explaining the concepts..."):
                    result = gemini_text(
                        "Identify and explain the most important concepts in the following "
                        "study material in beginner-friendly language, using small examples.\n\n"
                        + text[:50000]
                    )
                st.markdown(result)
            except Exception as exc:
                st.error(str(exc))

    question = st.text_input("Ask a question about the material")
    if st.button("Answer Question", use_container_width=True):
        if not question.strip():
            st.warning("Enter a question first.")
        else:
            try:
                with st.spinner("Finding the answer..."):
                    answer = gemini_text(
                        "Answer the question using only the supplied study material. "
                        "If the material does not contain enough information, say so clearly.\n\n"
                        f"MATERIAL:\n{text[:50000]}\n\nQUESTION:\n{question}"
                    )
                st.markdown(answer)
            except Exception as exc:
                st.error(str(exc))


def render_quiz() -> None:
    st.header("🎯 AI Quiz Generator")
    col1, col2 = st.columns(2)
    with col1:
        topic = st.text_input("Quiz topic", placeholder="Operating Systems: CPU scheduling")
        difficulty = st.select_slider("Difficulty", ["Easy", "Medium", "Hard"], value="Medium")
    with col2:
        count = st.slider("Questions", 3, 10, 5)
        source = st.text_area("Optional source material", height=120)

    if st.button("Generate Quiz", type="primary", use_container_width=True):
        if not topic.strip():
            st.warning("Enter a quiz topic.")
            return
        prompt = f"""
Create exactly {count} multiple-choice questions about {topic} at {difficulty} difficulty.
{('Use this source material and do not invent unsupported facts:\n' + source[:30000]) if source.strip() else ''}

Return ONLY JSON in this shape:
{{
  "title": "...",
  "questions": [
    {{
      "question": "...",
      "options": ["A", "B", "C", "D"],
      "correct_index": 0,
      "explanation": "..."
    }}
  ]
}}
"""
        try:
            with st.spinner("Generating quiz..."):
                raw = gemini_text(prompt, json_mode=True)
            quiz = safe_json(raw)
            if not quiz or not isinstance(quiz.get("questions"), list):
                raise RuntimeError("Gemini returned an invalid quiz format.")
            st.session_state.quiz = quiz
            st.session_state.answers = {}
        except Exception as exc:
            st.error(str(exc))

    quiz = st.session_state.quiz
    if not quiz:
        return

    st.subheader(quiz.get("title", "Quiz"))
    questions = quiz.get("questions", [])
    for index, question in enumerate(questions):
        options = question.get("options", [])
        if not isinstance(options, list) or len(options) != 4:
            continue
        st.markdown(f"**{index + 1}. {question.get('question', '')}**")
        answer = st.radio(
            "Choose one",
            options,
            key=f"quiz_{index}",
            index=None,
        )
        if answer is not None:
            st.session_state.answers[index] = options.index(answer)

    if st.button("Submit Quiz", use_container_width=True):
        score = 0
        graded = []
        for index, question in enumerate(questions):
            correct = question.get("correct_index")
            selected = st.session_state.answers.get(index)
            is_correct = selected == correct
            score += int(is_correct)
            graded.append(is_correct)
        st.session_state.quiz_history.append(
            {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "topic": quiz.get("title", "Quiz"),
                "score": score,
                "total": len(questions),
            }
        )
        st.success(f"Score: {score}/{len(questions)}")
        for index, question in enumerate(questions):
            selected = st.session_state.answers.get(index)
            correct = question.get("correct_index")
            label = "Correct" if selected == correct else "Review"
            with st.expander(f"Question {index + 1}: {label}"):
                st.write(f"Correct answer: {question.get('options', [])[correct]}")
                st.write(question.get("explanation", ""))


def render_progress() -> None:
    st.header("📊 Progress")
    plans = st.session_state.study_history
    quizzes = st.session_state.quiz_history

    c1, c2, c3 = st.columns(3)
    c1.metric("Study plans", len(plans))
    c2.metric("Quizzes completed", len(quizzes))
    avg = (
        sum(item["score"] / max(item["total"], 1) for item in quizzes) / len(quizzes) * 100
        if quizzes
        else 0
    )
    c3.metric("Average quiz score", f"{avg:.0f}%")

    st.subheader("Recent study plans")
    if plans:
        for item in reversed(plans[-10:]):
            st.write(
                f"{item['timestamp']} — {item['subject']} — {item['level']} — {item['weeks']} weeks"
            )
    else:
        st.info("No study plans yet.")

    st.subheader("Recent quizzes")
    if quizzes:
        for item in reversed(quizzes[-10:]):
            st.write(
                f"{item['timestamp']} — {item['topic']} — {item['score']}/{item['total']}"
            )
    else:
        st.info("No quiz results yet.")


def render_profile() -> None:
    st.header("👤 Profile")
    name = st.text_input("Name", value=st.session_state.profile.get("name", ""))
    course = st.text_input("Course / class", value=st.session_state.profile.get("course", ""))
    goals = st.text_area("Long-term goals", value=st.session_state.profile.get("goals", ""))
    if st.button("Save Profile", use_container_width=True):
        st.session_state.profile = {
            "name": name.strip(),
            "course": course.strip(),
            "goals": goals.strip(),
        }
        st.success("Profile saved for this session.")


def render_sidebar() -> str:
    with st.sidebar:
        st.title("AI Study Coach")
        page = st.radio(
            "Navigate",
            ["Study Plan", "Document Learning", "Quiz Generator", "Progress", "Profile"],
        )
        st.divider()
        api_key = get_api_key()
        if api_key:
            st.success("Gemini API configured")
            st.caption(f"Model: {MODEL_NAME}")
        else:
            st.warning("Gemini API key not configured")
            st.caption("Add GOOGLE_API_KEY in Streamlit secrets to enable AI features.")
    return page


def main() -> None:
    init_state()
    render_header()
    page = render_sidebar()

    if page == "Study Plan":
        render_study_plan()
    elif page == "Document Learning":
        render_document_learning()
    elif page == "Quiz Generator":
        render_quiz()
    elif page == "Progress":
        render_progress()
    else:
        render_profile()

    st.divider()
    st.caption("AI Study Coach · Streamlit + Google Gemini")


if __name__ == "__main__":
    main()
