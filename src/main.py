# AI Study Coach - Main Orchestrator
# Multi-Agent System Demonstration

import os
import asyncio
from dataclasses import dataclass
from typing import List, Dict
from loguru import logger

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
        """Stub agent for study planning"""
        return f"Study plan for {student.name} in {', '.join(student.subjects)}"
    
    async def quiz_generator_agent(self, student: StudentProfile, plan: str):
        """Stub agent for quiz generation"""
        return {"questions": ["Sample question 1", "Sample question 2"]}
    
    async def resource_agent(self, student: StudentProfile):
        """Stub agent for resource recommendation"""
        return ["Resource 1", "Resource 2"]
    
    async def progress_tracker_agent(self, student: StudentProfile, quiz: dict):
        """Stub agent for progress tracking"""
        return {"score": 85}

# Streamlit UI
import streamlit as st

st.set_page_config(page_title="🎓 AI Study Coach", page_icon="🎓", layout="wide")

st.title("🎓 AI Study Coach - Multi-Agent System")
st.markdown("### Intelligent Study Planning for Rural STEM Education")

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
    
    api_key = st.text_input("Google API Key", type="password", 
                            value=os.getenv("GOOGLE_API_KEY", ""))
    
    if st.button("🚀 Start Study Session", use_container_width=True):
        if not api_key:
            st.error("Please provide a Google API Key")
        elif not subjects:
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
        
