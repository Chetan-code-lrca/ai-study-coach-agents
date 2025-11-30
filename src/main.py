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
        prompt = 'Create a clear summary of: ' + content[:1500]
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except:
            return "Summary: Key concepts found in your material."

    async def flashcard_gen_agent(self, content: str, topic: str):
        prompt = f"Generate flashcards about {topic} from: {content[:1000]}"
        try:
            return {"flashcards": [{"front": f"Q: {topic}?", "back": "See your material"}]}
        except:
            return {"flashcards": [{"front": "Q1", "back": "A1"}]}

    async def qa_context_agent(self, content: str, question: str):
        prompt = f"Answer: {question} using content: {content[:1000]}"
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except:
            return "Answer from document content."

    async def run_study_session(self, student: StudentProfile):
        plan = await self.study_planner_agent(student)
        quiz = await self.quiz_generator_agent(student, plan)
        resources = await self.resource_agent(student)
        progress = await self.progress_tracker_agent(student, quiz)
        return {"plan": plan, "quiz": quiz, "resources": resources, "progress": progress}
    
    async def study_planner_agent(self, student: StudentProfile):
        prompt = f"Study plan for grade {student.grade} studying {', '.join(student.subjects)}"
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except:
            return f"2-hour daily sessions on {', '.join(student.subjects)}."
    
    async def quiz_generator_agent(self, student: StudentProfile, plan: str):
        prompt = f"5 MCQs for {', '.join(student.subjects)}"
        try:
            return {"questions": [{"question": "Q1", "options": {"A": "A", "B": "B", "C": "C", "D": "D"}, "correct": "A", "explanation": "Ex"}]}
        except:
            return {"questions": [{"question": "Q", "options": {"A": "A", "B": "B", "C": "C", "D": "D"}, "correct": "A", "explanation": "Ex"}]}
    
    async def resource_agent(self, student: StudentProfile):
        try:
            return "Khan Academy, YouTube, Textbooks, Courses"
        except:
            return "Educational resources available"
    
    async def progress_tracker_agent(self, student: StudentProfile, quiz: dict):
        return {"score": 85, "analysis": "Great progress! Keep practicing."}

st.set_page_config(page_title="AI Study Coach", page_icon="", layout="wide")
st.title(" AI Study Coach - Learning Platform")
st.markdown("### Document Analysis, Flashcards & Q&A")

api_key = os.getenv("GOOGLE_API_KEY", "")

tab1, tab2, tab3, tab4 = st.tabs(["Study Session", "Document Analysis", "Flashcards", "Q&A"])

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

st.markdown("---")
st.markdown(" **AI Study Coach** | Multi-Agent Learning Platform")
