"""Streamlit Frontend for AI Study Coach - Standalone Version.

Interactive web interface for students to access the AI study coach system.
"""

import streamlit as st
import os

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
.feature-box {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 20px;
    border-radius: 10px;
    margin: 10px 0;
}
</style>
""", unsafe_allow_html=True)


def init_session_state():
    """Initialize Streamlit session state."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "student_demo"
        st.session_state.study_history = []
        st.session_state.quiz_results = []


def main():
    """Main application entry point."""
    init_session_state()
    
    # Header
    st.markdown('<p class="big-font">🎓 AI Study Coach</p>', unsafe_allow_html=True)
    st.markdown("**Empowering Rural STEM Education with Multi-Agent AI**")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.title("🎯 Navigation")
        page = st.radio(
            "Choose a feature:",
            ["📚 Study Plan", "✏️ Quiz Generator", "📊 Progress Analytics", "🔍 Resource Finder"]
        )
        
        st.markdown("---")
        st.markdown("### About This Project")
        st.info(
            "This AI Study Coach uses multiple specialized agents powered by Google Gemini "
            "to provide personalized STEM education support for rural students."
        )
        
        st.markdown("### 🛠️ Technology")
        st.markdown("""
        - Google Gemini 2.0
        - Multi-Agent System
        - Firebase Backend
        - Python + Streamlit
        """)
        
        st.markdown("---")
        st.markdown("### 📂 Links")
        st.markdown("[GitHub Repository](https://github.com/Chetan-code-lrca/ai-study-coach-agents)")
        st.markdown("[Documentation](https://chetan-code-lrca.github.io/ai-study-coach-agents/)")
    
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
                st.success("✅ Study plan generated successfully!")
                st.markdown("### Your Personalized Study Plan")
                
                # Mock study plan
                st.markdown(f"""
                #### {topic} Study Plan - {duration} Weeks ({level} Level)
                
                **Week 1-{min(2, duration)}**: Foundation Building
                - Review fundamental concepts (30 min/day)
                - Watch video tutorials from Khan Academy
                - Complete practice problems (45 min/day)
                - Take notes and create flashcards
                
                **Week {min(3, duration)}-{min(4, duration)}**: Deep Dive
                - Advanced topics and applications
                - Group study sessions (recommended)
                - Mock quizzes (1x per week)
                - Project-based learning
                
                **Focus Areas**:
                - Core {topic} principles
                - Problem-solving techniques
                - Real-world applications
                
                **Resources**:
                - 📚 Recommended textbooks
                - 🎥 Video tutorials
                - 📝 Practice worksheets
                - 💬 Study groups
                """)
                
                # Save to history
                st.session_state.study_history.append({
                    "topic": topic,
                    "duration": duration,
                    "level": level
                })
                
                st.balloons()
    
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
                    st.success("✅ Quiz generated!")
                    st.markdown("### Your Quiz")
                    
                    # Mock quiz
                    for i in range(min(num_questions, 5)):
                        st.markdown(f"""\n**Question {i+1}**: What is a key concept in {quiz_topic}?
                        
A) Option A  
B) Option B  
C) Option C  
D) Option D
                        """)
                        st.radio(f"Your answer for Q{i+1}:", ["A", "B", "C", "D"], key=f"q{i}")
                    
                    if st.button("Submit Quiz"):
                        score = 80  # Mock score
                        st.session_state.quiz_results.append({
                            "topic": quiz_topic,
                            "score": score,
                            "difficulty": difficulty
                        })
                        st.success(f"🎉 Your Score: {score}%")
            else:
                st.warning("Please enter a quiz topic.")
    
    elif "Progress" in page:
        st.header("📊 Progress Analytics")
        st.markdown("Track your learning journey and identify areas for improvement.")
        
        # Display metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_score = 75 if st.session_state.quiz_results else 0
            st.metric(
                "Average Score",
                f"{avg_score}%",
                "+5%"
            )
        
        with col2:
            total_quizzes = len(st.session_state.quiz_results)
            st.metric(
                "Total Quizzes",
                total_quizzes
            )
        
        with col3:
            total_plans = len(st.session_state.study_history)
            st.metric(
                "Study Plans Created",
                total_plans
            )
        
        # Insights
        st.markdown("### 💡 Insights")
        if st.session_state.quiz_results or st.session_state.study_history:
            st.info("✓ Great progress! Keep up the consistent study habits.")
            st.info("✓ Your performance is improving over time.")
            st.info("✓ Consider focusing more time on challenging topics.")
        else:
            st.warning("Start taking quizzes and creating study plans to see your progress!")
        
        # Show study history
        if st.session_state.study_history:
            st.markdown("### 📚 Recent Study Plans")
            for idx, session in enumerate(st.session_state.study_history[-5:]):
                st.markdown(f"{idx+1}. {session['topic']} ({session['duration']} weeks, {session['level']} level)")
        
        # Quiz history
        if st.session_state.quiz_results:
            st.markdown("### ✏️ Recent Quiz Results")
            for idx, quiz in enumerate(st.session_state.quiz_results[-5:]):
                st.markdown(f"{idx+1}. {quiz['topic']} - Score: {quiz['score']}% ({quiz['difficulty']})")
    
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
                    
                    if "Videos" in resource_types:
                        st.markdown("#### 📺 Video Resources")
                        st.markdown(f"- [Khan Academy: Introduction to {resource_topic}](https://khanacademy.org)")
                        st.markdown(f"- [YouTube: {resource_topic} Explained](https://youtube.com)")
                        st.markdown(f"- [Crash Course: {resource_topic}](https://youtube.com/crashcourse)")
                    
                    if "Articles" in resource_types:
                        st.markdown("#### 📄 Article Resources")
                        st.markdown(f"- Complete Guide to {resource_topic}")
                        st.markdown(f"- Step-by-Step Tutorial: {resource_topic}")
                        st.markdown(f"- {resource_topic}: Beginner to Advanced")
                    
                    if "Practice" in resource_types:
                        st.markdown("#### ✍️ Practice Resources")
                        st.markdown(f"- {resource_topic} Practice Problems")
                        st.markdown(f"- Interactive Exercises for {resource_topic}")
                        st.markdown(f"- {resource_topic} Worksheets")
                    
                    if "Interactive" in resource_types:
                        st.markdown("#### 🎮 Interactive Resources")
                        st.markdown(f"- {resource_topic} Simulator")
                        st.markdown(f"- Interactive {resource_topic} Lab")
                        st.markdown(f"- {resource_topic} Visualization Tools")
            else:
                st.warning("Please enter a topic to search.")
    
    # Footer
    st.markdown("---")
    st.markdown(
        "<div style='text-align: center'>"  
        "<p>🏆 Kaggle Agents Intensive Capstone Project | Track: Agents for Good</p>"
        "<p>Powered by Google Gemini 2.0 | Built by Chetan</p>"
        "<p><a href='https://github.com/Chetan-code-lrca/ai-study-coach-agents'>View on GitHub</a></p>"
        "</div>",
        unsafe_allow_html=True
    )


if __name__ == "__main__":
    main()
