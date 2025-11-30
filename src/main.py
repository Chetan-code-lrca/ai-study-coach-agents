# Enhanced: Document Processing & Advanced Features
# AI Study Coach - Learning Platform

import os
import asyncio
from dataclasses import dataclass
from typing import List, Dict
from loguru import logger
import google.generativeai as genai
import json
import re
import streamlit as st
from datetime import datetime
from pathlib import Path
import csv

logger.add("logs/study_coach_{time}.log", rotation="1 day")

@dataclass
class StudentProfile:
    student_id: str
    name: str
    grade: int
    subjects: List[str]
    weak_topics: List[str] = None

class AgentOrchestrator:
    def __init__(self, gemini_api_key: str):
        self.api_key = gemini_api_key
        self.sessions = {}
        logger.info("Orchestrator initialized")
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')

    async def document_summarizer_agent(self, content: str):
        prompt = 'Create a clear summary of this content: ' + content[:2000] + ' Provide: 1. Overview 2. Key points 3. Summary'
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Summary error: {e}")
            return "Could not generate summary"

    async def flashcard_gen_agent(self, content: str, topic: str):
        prompt = f'Generate 5 flashcards for {topic} based on: {content[:1000]} Format: [{{"front": "Q", "back": "A"}}]'
        try:
            response = self.model.generate_content(prompt)
            import re
            cards_text = response.text
            cards_match = re.search(r'\[.*\]', cards_text, re.DOTALL)
            if cards_match:
                cards_json = cards_match.group()
                flashcards = json.loads(cards_json)
                return {"flashcards": flashcards}
            return {"flashcards": []}
        except Exception as e:
            logger.error(f"Flashcard error: {e}")
            return {"flashcards": []}

    async def qa_context_agent(self, document: str, question: str):
        prompt = f'Based on this document: {document[:1000]} Answer: {question}'
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"QA error: {e}")
            return "Could not answer question"

    async def run_study_session(self, student: StudentProfile):
        return {
            "plan": f"Study plan for {student.name} - Subjects: {', '.join(student.subjects)}",
            "quiz": "Quiz questions will be generated",
            "resources": "Recommended resources"
        }

class DataManager:
    def __init__(self, data_dir: str = ".study_coach_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        self.user_file = self.data_dir / "user_profile.json"
        self.sessions_file = self.data_dir / "work_sessions.csv"

    def save_user_data(self, user_data: Dict):
        try:
            with open(self.user_file, 'w') as f:
                json.dump(user_data, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving user data: {e}")
            return False

    def load_user_data(self) -> Dict:
        try:
            if self.user_file.exists():
                with open(self.user_file, 'r') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.error(f"Error loading user data: {e}")
            return {}

    def save_work_session(self, session_data: Dict):
        try:
            file_exists = self.sessions_file.exists()
            with open(self.sessions_file, 'a', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=['date', 'subject', 'duration', 'notes', 'files_analyzed'])
                if not file_exists:
                    writer.writeheader()
                writer.writerow(session_data)
            return True
        except Exception as e:
            logger.error(f"Error saving session: {e}")
            return False

    def load_work_sessions(self) -> list:
        try:
            if self.sessions_file.exists():
                sessions = []
                with open(self.sessions_file, 'r') as f:
                    reader = csv.DictReader(f)
                    sessions = list(reader)
                return sessions
            return []
        except Exception as e:
            logger.error(f"Error loading sessions: {e}")
            return []

st.set_page_config(page_title="AI Study Coach", page_icon="🎓", layout="wide")
st.title("AI Study Coach - Learning Platform")
st.markdown("### Document Analysis, Flashcards & Q&A")

api_key = os.getenv("GOOGLE_API_KEY", "")
data_manager = DataManager()

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Study Session", "Document Analysis", "Flashcards", "Q&A", "User Profile", "History"])

with tab1:
    st.header("Create Study Session")
    col1, col2 = st.columns(2)
    with col1:
        name = st.text_input("Name", "John Doe")
        grade = st.selectbox("Grade", list(range(6, 13)), index=4)
        subjects = st.multiselect("Subjects", ["Math", "Physics", "Chemistry", "Biology", "CS"], default=["Math"])
    with col2:
        if st.button(" Start Session", use_container_width=True):
            if not api_key:
                st.error("API key not set")
            else:
                orch = AgentOrchestrator(api_key)
                student = StudentProfile("001", name, grade, subjects)
                result = asyncio.run(orch.run_study_session(student))
                st.success("Session created!")
                st.write(result["plan"][:300])

with tab2:
    st.header("Document Summary")
    content = st.text_area("Paste text:", height=200)
    if st.button(" Analyze", use_container_width=True):
        if content and api_key:
            orch = AgentOrchestrator(api_key)
            summary = asyncio.run(orch.document_summarizer_agent(content))
            st.success("Summary:")
            st.write(summary[:500])

with tab3:
    st.header("Generate Flashcards")
    fc_content = st.text_area("Material:", height=200, key="fc")
    fc_topic = st.text_input("Topic:")
    if st.button(" Generate", use_container_width=True):
        if fc_content and api_key:
            orch = AgentOrchestrator(api_key)
            fc = asyncio.run(orch.flashcard_gen_agent(fc_content, fc_topic))
            for i, card in enumerate(fc.get("flashcards", [])[:3], 1):
                st.write(f"{i}. {card.get('front')} => {card.get('back')}")

with tab4:
    st.header("Q&A from Document")
    qa_content = st.text_area("Document:", height=200, key="qa")
    qa_question = st.text_input("Question:")
    if st.button(" Answer", use_container_width=True):
        if qa_content and qa_question and api_key:
            orch = AgentOrchestrator(api_key)
            answer = asyncio.run(orch.qa_context_agent(qa_content, qa_question))
            st.success("Answer:")
            st.write(answer[:500])

with tab5:
    st.header("User Profile & File Upload")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Personal Information")
        user_name = st.text_input("Full Name", value="")
        user_email = st.text_input("Email", value="")
        user_grade = st.selectbox("Grade Level", list(range(6, 13)))
        user_subjects = st.multiselect("Subjects Studying", ["Math", "Physics", "Chemistry", "Biology", "CS", "English", "History"])
        user_learning_style = st.selectbox("Learning Style", ["Visual", "Auditory", "Reading/Writing", "Kinesthetic"])
        
        if st.button("Save Profile", use_container_width=True):
            user_data = {
                "name": user_name,
                "email": user_email,
                "grade": user_grade,
                "subjects": user_subjects,
                "learning_style": user_learning_style,
                "last_updated": datetime.now().isoformat()
            }
            if data_manager.save_user_data(user_data):
                st.success("Profile saved successfully!")
            else:
                st.error("Error saving profile")
    
    with col2:
        st.subheader("File Upload & Documents")
        
        uploaded_file = st.file_uploader("Upload Study Material", type=["txt", "pdf", "csv", "json"])
        
        if uploaded_file is not None:
            if uploaded_file.type == "text/plain":
                file_content = uploaded_file.read().decode("utf-8")
                st.success(f"File loaded: {uploaded_file.name}")
                st.text_area("File Content:", value=file_content[:500], height=150, disabled=True)
        
        st.subheader("Work Session Log")
        session_subject = st.selectbox("Subject Studied", ["Math", "Physics", "Chemistry", "Biology", "CS"])
        session_duration = st.number_input("Duration (minutes)", min_value=15, max_value=240, step=15)
        session_notes = st.text_area("Session Notes", height=100)
        
        if st.button("Log Work Session", use_container_width=True):
            session_data = {
                "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "subject": session_subject,
                "duration": session_duration,
                "notes": session_notes,
                "files_analyzed": uploaded_file.name if uploaded_file else "None"
            }
            if data_manager.save_work_session(session_data):
                st.success("Session logged successfully!")
            else:
                st.error("Error logging session")

with tab6:
    st.header("Study History & Insights")
    
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("User Profile")
        user_data = data_manager.load_user_data()
        if user_data:
            st.write(f"**Name:** {user_data.get('name', 'Not set')}")
            st.write(f"**Email:** {user_data.get('email', 'Not set')}")
            st.write(f"**Grade:** {user_data.get('grade', 'Not set')}")
            st.write(f"**Subjects:** {', '.join(user_data.get('subjects', []))}")
            st.write(f"**Learning Style:** {user_data.get('learning_style', 'Not set')}")
        else:
            st.info("No profile data saved yet. Please create a profile first.")
    
    with col2:
        st.subheader("Work Sessions")
        sessions = data_manager.load_work_sessions()
        if sessions:
            for session in sessions[-10:]:  # Show last 10 sessions
                st.write(f"**{session['date']}** - {session['subject']} ({session['duration']} min)")
                st.caption(session['notes'][:100] if session['notes'] else "No notes")
        else:
            st.info("No work sessions logged yet.")

st.markdown("---")
st.markdown(" **AI Study Coach** | Multi-Agent Learning Platform")
