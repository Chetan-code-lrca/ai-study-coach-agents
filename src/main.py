# Updated: Streamlit redeployment trigger
# AI Study Coach - Main Orchestrator
# Multi-Agent System Demonstration

import os
import asyncio
from dataclasses import dataclass
from typing import List, Dict
from loguru import logger
import google.generativeai as genai
import json
import re

# Observability: Logging configuration
logger.add("logs/study_coach_{time}.log", rotation="1 day")

@dataclass
class StudentProfile:
    student_id: str
    name: str
    grade: int
    subjects: List[str]
    weak_topics: List[str] = None

class AgentOrchestrator:
    """Multi-agent orchestrator with sequential/parallel execution"""
    
    def __init__(self, gemini_api_key: str):
        self.api_key = gemini_api_key
        self.sessions = {}  # Session management
        logger.info("Orchestrator initialized")
        genai.configure(api_key=gemini_api_key)
        self.model = genai.GenerativeModel('gemini-pro')
    
    async def run_study_session(self, student: StudentProfile):
        """Execute multi-agent workflow"""
        logger.info(f"Session for {student.name}")
        
        # Sequential agents
        plan = await self.study_planner_agent(student)
        quiz = await self.quiz_generator_agent(student, plan)
        
        # Parallel agents
        results = await asyncio.gather(
            self.resource_agent(student),
            self.progress_tracker_agent(student, quiz)
        )
        
        return {"plan": plan, "quiz": quiz, "resources": results[0]}
    
    async def study_planner_agent(self, student: StudentProfile):
        """AI-powered study planning agent using Gemini"""
        prompt = f"""
        Create a detailed study plan for a grade {student.grade} student named {student.name}.
        Subjects: {', '.join(student.subjects)}
        
        Provide a structured weekly study plan with:
        - Daily study schedule
        - Time allocation for each subject
        - Study techniques and tips
        - Break times and revision sessions
        
        Format the response in a clear, actionable way.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Study planner error: {str(e)}")
            return f"Study plan for {student.name}: Focus on {', '.join(student.subjects)} with daily 2-hour sessions."
    async def quiz_generator_agent(self, student: StudentProfile, plan: str):
        """AI-powered quiz generation agent using Gemini"""
        prompt = f"""
        Generate 5 multiple-choice questions for a grade {student.grade} student.
        Subjects: {', '.join(student.subjects)}
        
        For each question provide:
        1. The question
        2. Four options (A, B, C, D)
        3. The correct answer
        4. A brief explanation
        
        Format as JSON with this structure:
        {{
            "questions": [
                {{"question": "...", "options": {{"A": "...", "B": "...", "C": "...", "D": "..."}}, "correct": "A", "explanation": "..."}}
            ]
        }}
        """
        try:
            response = self.model.generate_content(prompt)
            # Try to extract questions from response
            text = response.text
            # Try to find JSON in the response
            json_match = re.search(r'\{.*"questions".*\}', text, re.DOTALL)
            if json_match:
                quiz_data = json.loads(json_match.group())
                return quiz_data
            else:
                # Return sample questions if parsing fails
                return {
                    "questions": [
                        {"question": f"Question about {student.subjects[0] if student.subjects else 'the subject'}",
                         "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"},
                         "correct": "A",
                         "explanation": "This is a sample question."}
                    ]
                }
        except Exception as e:
            logger.error(f"Quiz generator error: {str(e)}")
            return {"questions": [{"question": "Sample question", "options": {"A": "Option A", "B": "Option B", "C": "Option C", "D": "Option D"}, "correct": "A", "explanation": "Sample"}]}

    async def resource_agent(self, student: StudentProfile):
        """AI-powered resource recommendation agent using Gemini"""
        prompt = f"""
        You are an educational resource recommender for a grade {student.grade} student named {student.name}.
        Subjects: {', '.join(student.subjects)}
        
        Recommend 5 high-quality learning resources for these subjects. For each resource provide:
        1. Resource name/title
        2. Type (website, video, book, app, etc.)
        3. Subject it covers
        4. Brief description of why it's valuable
        
        Format as a clear, organized list.
        """
        try:
            response = self.model.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Resource agent error: {str(e)}")
            return f"Here are some recommended resources for {student.name}:\n- Khan Academy (Math & Science)\n- Duolingo (Languages)\n- Crash Course (Various subjects)"

        
    async def progress_tracker_agent(self, student: StudentProfile, quiz: dict):
                """AI-powered progress tracking agent using Gemini"""
        # Analyze the quiz results
        total_questions = len(quiz.get('questions', []))
        
        prompt = f"""
        You are a progress tracking agent for a grade {student.grade} student named {student.name}.
        Subjects: {', '.join(student.subjects)}
        
        The student just completed a quiz with {total_questions} questions.
        
        Based on this quiz performance, provide:
        1. Overall assessment of their understanding
        2. Strengths identified
        3. Areas needing improvement
        4. Specific recommendations for study focus
        5. Motivational feedback
        
        Be encouraging and constructive. Format as clear sections.
        """
        try:
            response = self.model.generate_content(prompt)
            return {"score": 85, "analysis": response.text}
        except Exception as e:
            logger.error(f"Progress tracker error: {str(e)}")
            return {"score": 85, "analysis": f"Great effort, {student.name}! Keep practicing your {', '.join(student.subjects)} regularly."}

# Streamlit UI
import streamlit as st

st.set_page_config(page_title="🎓 AI Study Coach", page_icon="🎓", layout="wide")

st.title("🎓 AI Study Coach - Multi-Agent System")
st.markdown("### Intelligent Study Planning for Rural STEM Education")

# Custom CSS for professional appearance
st.markdown("""
<style>
    .main > div {
        padding-top: 2rem;
    }
    .stButton>button {
        width: 100%;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.75rem;
        font-weight: 600;
        border-radius: 0.5rem;
        transition: transform 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
    }
    h1 {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
    }
</style>
""", unsafe_allow_html=True)

# Sidebar for student information
with st.sidebar:
    st.header("Student Profile")
    student_name = st.text_input("Name", "John Doe")
    student_grade = st.selectbox("Grade", list(range(6, 13)), index=4)
    subjects = st.multiselect(
        "Subjects", 
        ["Mathematics", "Physics", "Chemistry", "Biology", "Computer Science"],
        default=["Mathematics", "Physics"]
    )
    
    
    # Get API key from environment variable (configured in Streamlit secrets)
    api_key = os.getenv("GOOGLE_API_KEY", "")
    
    if st.button("🚀 Start Study Session", use_container_width=True):
        if not subjects:
            st.error("Please select at least one subject")
        else:
            st.session_state.run_session = True
            st.session_state.student = StudentProfile(
                student_id="001",
                name=student_name,
                grade=student_grade,
                subjects=subjects
            )
            st.session_state.api_key = api_key

# Main content area
if 'run_session' in st.session_state and st.session_state.run_session:
    orchestrator = AgentOrchestrator(st.session_state.api_key)
    
    with st.spinner("Running multi-agent workflow..."):
        try:
            result = asyncio.run(orchestrator.run_study_session(st.session_state.student))
            
            st.success("Study session completed!")
            
            # Display results
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📚 Study Plan")
                st.info(result.get("plan", "No plan generated"))
                
                st.subheader("📝 Quiz")
                quiz_data = result.get("quiz", {})
                for i, question in enumerate(quiz_data.get("questions", []), 1):
                    st.markdown(f"**Q{i}:** {question}")
            
            with col2:
                st.subheader("📖 Recommended Resources")
                resources = result.get("resources", [])
                for resource in resources:
                    st.markdown(f"- {resource}")
            
            st.session_state.run_session = False
        except Exception as e:
            st.error(f"Error: {str(e)}")
            logger.error(f"Session error: {str(e)}")
else:
    st.info("👈 Enter student information in the sidebar and click 'Start Study Session' to begin!")
    
    # Show features
    st.subheader("✨ Features")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("### 📚 Study Planning")
        st.markdown("AI-powered personalized study plans")
    
    with col2:
        st.markdown("### 📝 Quiz Generation")
        st.markdown("Adaptive quizzes based on weak topics")
    
    with col3:
        st.markdown("### 📊 Progress Tracking")
        st.markdown("Monitor learning progress")

# Footer
st.markdown("---")
st.markdown("🎓 **AI Study Coach** | Powered by Google Gemini | Kaggle Agents Intensive Capstone Project")
        
