"""Streamlit Frontend for AI Study Coach.

Interactive web interface for students to access the multi-agent study coach system.
"""

import streamlit as st
import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.main import AIStudyCoach
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Page configuration
st.set_page_config(
    page_title="AI Study Coach",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.big-font {
    font-size:30px !important;
    font-weight: bold;
}
.highlight {
    background-color: #f0f2f6;
    padding: 20px;
    border-radius: 10px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize Streamlit session state."""
    if 'coach' not in st.session_state:
        st.session_state.coach = AIStudyCoach()
        st.session_state.user_id = "student_demo"
        st.session_state.study_history = []
        st.session_state.quiz_results = []


async def generate_study_plan(topic, level, duration):
    """Generate personalized study plan."""
    try:
        user_profile = {
            "name": "Rural Student",
            "level": level,
            "topics_of_interest": [topic],
            "study_duration": duration
        }
        
        result = await st.session_state.coach.create_study_plan(
            st.session_state.user_id,
            user_profile
        )
        return result
    except Exception as e:
        logger.error(f"Study plan generation failed: {e}")
        return {"error": str(e)}


async def generate_quiz(topic, difficulty, num_questions):
    """Generate quiz questions."""
    try:
        result = await st.session_state.coach.generate_quiz(
            st.session_state.user_id,
            topic=topic,
            difficulty=difficulty,
            num_questions=num_questions
        )
        return result
    except Exception as e:
        logger.error(f"Quiz generation failed: {e}")
        return {"error": str(e)}


async def get_progress_analytics():
    """Get student progress analytics."""
    try:
        # Mock user data for demonstration
        user_data = {
            "name": "Rural Student",
            "quiz_history": st.session_state.quiz_results,
            "study_sessions": st.session_state.study_history
        }
        
        from src.agents.progress_tracker import ProgressTrackerAgent
        tracker = ProgressTrackerAgent()
        result = await tracker.analyze_progress(
            st.session_state.user_id,
            user_data
        )
        return result
    except Exception as e:
        logger.error(f"Progress analytics failed: {e}")
        return {"error": str(e)}


def main():
    """Main application entry point."""
    init_session_state()
    
    # Header
    st.markdown('<p class="big-font">🎓 AI Study Coach</p>', unsafe_allow_html=True)
    st.markdown("**Empowering Rural STEM Education with Multi-Agent AI**")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.image("https://via.placeholder.com/150x150.png?text=AI+Coach", width=150)
        st.title("Navigation")
        page = st.radio(
            "Choose a feature:",
            ["📚 Study Plan", "✏️ Quiz Generator", "📊 Progress Analytics", "🔍 Resource Finder"]
        )
        
        st.markdown("---")
        st.markdown("### About")
        st.info(
            "This AI Study Coach uses multiple specialized agents powered by Google Gemini "
            "to provide personalized STEM education support."
        )
    
    # Main content based on selected page
    if "Study Plan" in page:
        st.header("📚 Personalized Study Plan Generator")
        st.markdown("Generate a customized study plan tailored to your learning needs.")
        
        col1, col2 = st.columns(2)
        with col1:
            topic = st.selectbox(
                "Select Topic",
                ["Physics", "Chemistry", "Mathematics", "Biology", "Computer Science"]
            )
            level = st.select_slider(
                "Your Level",
                options=["Beginner", "Intermediate", "Advanced"]
            )
        
        with col2:
            duration = st.slider(
                "Study Duration (weeks)",
                min_value=1,
                max_value=12,
                value=4
            )
            goals = st.text_area(
                "Learning Goals (optional)",
                placeholder="E.g., Prepare for exams, understand core concepts..."
            )
        
        if st.button("🎯 Generate Study Plan", type="primary"):
            with st.spinner("Creating your personalized study plan..."):
                result = asyncio.run(
                    generate_study_plan(topic, level.lower(), duration)
                )
                
                if "error" not in result:
                    st.success("✅ Study plan generated successfully!")
                    st.markdown("### Your Personalized Study Plan")
                    
                    study_plan = result.get('study_plan', {})
                    st.markdown(study_plan.get('text', 'No study plan available'))
                    
                    # Save to history
                    st.session_state.study_history.append({
                        "topic": topic,
                        "duration": duration,
                        "date": "today"
                    })
                else:
                    st.error(f"Error: {result['error']}")
    
    elif "Quiz" in page:
        st.header("✏️ Interactive Quiz Generator")
        st.markdown("Test your knowledge with AI-generated quizzes.")
        
        col1, col2 = st.columns(2)
        with col1:
            quiz_topic = st.text_input(
                "Quiz Topic",
                placeholder="E.g., Newton's Laws of Motion"
            )
            difficulty = st.select_slider(
                "Difficulty",
                options=["Easy", "Medium", "Hard"]
            )
        
        with col2:
            num_questions = st.number_input(
                "Number of Questions",
                min_value=3,
                max_value=20,
                value=5
            )
        
        if st.button("🎲 Generate Quiz", type="primary"):
            if quiz_topic:
                with st.spinner("Generating quiz questions..."):
                    result = asyncio.run(
                        generate_quiz(quiz_topic, difficulty.lower(), num_questions)
                    )
                    
                    if "error" not in result:
                        st.success("✅ Quiz generated!")
                        quiz_content = result.get('quiz', {})
                        st.markdown("### Your Quiz")
                        st.markdown(quiz_content.get('text', 'No quiz content available'))
                        
                        # Mock quiz results
                        st.session_state.quiz_results.append({
                            "topic": quiz_topic,
                            "score": 80,
                            "date": "today"
                        })
                    else:
                        st.error(f"Error: {result['error']}")
            else:
                st.warning("Please enter a quiz topic.")
    
    elif "Progress" in page:
        st.header("📊 Progress Analytics")
        st.markdown("Track your learning journey and identify areas for improvement.")
        
        if st.button("📈 Analyze My Progress"):
            with st.spinner("Analyzing your performance..."):
                result = asyncio.run(get_progress_analytics())
                
                if "error" not in result:
                    st.success("✅ Analysis complete!")
                    
                    # Display metrics
                    col1, col2, col3 = st.columns(3)
                    metrics = result.get('performance_metrics', {})
                    
                    with col1:
                        st.metric(
                            "Average Score",
                            f"{metrics.get('average_score', 0)}%",
                            f"+{metrics.get('improvement_rate', 0)}%"
                        )
                    
                    with col2:
                        st.metric(
                            "Total Quizzes",
                            metrics.get('total_quizzes', 0)
                        )
                    
                    with col3:
                        engagement = result.get('engagement_metrics', {})
                        st.metric(
                            "Study Consistency",
                            f"{engagement.get('consistency_score', 0)}/100"
                        )
                    
                    # Insights
                    st.markdown("### 💡 Insights")
                    insights = result.get('insights', [])
                    for insight in insights:
                        st.info(f"• {insight}")
                    
                    # Learning gaps
                    gaps = result.get('learning_gaps', [])
                    if gaps:
                        st.markdown("### 🎯 Areas to Focus")
                        for gap in gaps:
                            st.warning(
                                f"**{gap['topic']}**: Average {gap['average_score']}% "
                                f"({gap['severity']} priority)"
                            )
                else:
                    st.error(f"Error: {result['error']}")
        
        # Show study history
        if st.session_state.study_history:
            st.markdown("### 📚 Recent Study Sessions")
            for session in st.session_state.study_history[-5:]:
                st.markdown(f"- {session['topic']} ({session['duration']} weeks)")
    
    else:  # Resource Finder
        st.header("🔍 Learning Resource Finder")
        st.markdown("Discover curated educational resources from across the web.")
        
        col1, col2 = st.columns(2)
        with col1:
            resource_topic = st.text_input(
                "What do you want to learn?",
                placeholder="E.g., Quantum Physics"
            )
        
        with col2:
            resource_types = st.multiselect(
                "Resource Types",
                ["Videos", "Articles", "Practice", "Interactive"],
                default=["Videos", "Articles"]
            )
        
        if st.button("🔎 Find Resources", type="primary"):
            if resource_topic:
                with st.spinner("Searching for resources..."):
                    st.success("✅ Found educational resources!")
                    st.markdown("### Recommended Resources")
                    
                    # Mock resources
                    st.markdown("#### 📺 Video Resources")
                    st.markdown("- Khan Academy: Introduction to " + resource_topic)
                    st.markdown("- YouTube: " + resource_topic + " Explained")
                    
                    st.markdown("#### 📄 Article Resources")
                    st.markdown("- Complete Guide to " + resource_topic)
                    st.markdown("- Step-by-Step Tutorial: " + resource_topic)
            else:
                st.warning("Please enter a topic to search.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center'>Powered by Google Gemini | "
        "Built for Kaggle Agents Intensive Capstone | Agents for Good</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
