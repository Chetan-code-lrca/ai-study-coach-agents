"""Streamlit Frontend for AI Study Coach - With Gemini Quiz Generation.

Interactive web interface for students to access the AI study coach system.
"""
import streamlit as st
import os
import json
import google.generativeai as genai

# Configure Gemini API
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if GOOGLE_API_KEY:
    genai.configure(api_key=GOOGLE_API_KEY)

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
    /* Global Styles */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main Header Styling */
    .big-font {
        font-size: 2.5rem !important;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    /* Highlight Boxes */
    .highlight {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    
    .highlight:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
    }
    
    /* Feature Box - Modern Gradient Cards */
    .feature-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 20px;
        margin: 1.5rem 0;
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.4);
        transition: all 0.3s ease;
    }
    
    .feature-box:hover {
        transform: scale(1.03);
        box-shadow: 0 15px 40px rgba(102, 126, 234, 0.6);
    }
    
    /* Button Enhancements */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 0.75rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4) !important;
    }
    
    .stButton>button:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6) !important;
    }
    
    /* Input Fields */
    .stTextInput>div>div>input {
        border-radius: 10px !important;
        border: 2px solid #e0e0e0 !important;
        padding: 0.75rem !important;
        transition: all 0.3s ease !important;
    }
    
    .stTextInput>div>div>input:focus {
        border-color: #667eea !important;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1) !important;
    }
    
    /* Success/Error Messages */
    .stSuccess {
        background: linear-gradient(135deg, #84fab0 0%, #8fd3f4 100%) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }
    
    .stError {
        background: linear-gradient(135deg, #fa709a 0%, #fee140 100%) !important;
        border-radius: 10px !important;
        padding: 1rem !important;
    }
    
    /* Animations */
    @keyframes fadeIn {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
    
    .main > div {
        animation: fadeIn 0.5s ease;
    }
</style>
""", unsafe_allow_html=True)

def init_session_state():
    """Initialize Streamlit session state."""
    if 'user_id' not in st.session_state:
        st.session_state.user_id = "student_demo"
    if 'study_history' not in st.session_state:
        st.session_state.study_history = []
    if 'quiz_results' not in st.session_state:
        st.session_state.quiz_results = []

def generate_quiz_with_gemini(topic, difficulty, num_questions):
    """Generate quiz using Google Gemini API."""
    try:
        if not GOOGLE_API_KEY:
            st.error("⚠️ Google API Key not configured. Please set GOOGLE_API_KEY in Streamlit secrets.")
            return None
        
        # Create prompt for quiz generation
        prompt = f"""
You are an expert educator creating a quiz for students studying in rural areas with limited resources.

Generate a {difficulty} difficulty quiz about: {topic}

Requirements:
- Create exactly {num_questions} multiple-choice questions
- Each question should have 4 options (A, B, C, D)
- Mark the correct answer
- Include a brief explanation for each answer
- Make questions practical and relevant to rural students
- Focus on conceptual understanding

Return ONLY a valid JSON object in this exact format:
{{
    "quiz_title": "{topic} Quiz",
    "difficulty": "{difficulty}",
    "questions": [
        {{
            "question": "Question text here?",
            "options": {{
                "A": "Option A text",
                "B": "Option B text",
                "C": "Option C text",
                "D": "Option D text"
            }},
            "correct_answer": "A",
            "explanation": "Explanation why A is correct"
        }}
    ]
}}
"""
        
        # Generate content using Gemini
        model = genai.GenerativeModel('gemini-2.0-flash-001')
        response = model.generate_content(prompt)
        
        # Parse JSON response
        response_text = response.text.strip()
        # Remove markdown code blocks if present
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
        response_text = response_text.strip()
        
        quiz_data = json.loads(response_text)
        return quiz_data
        
    except json.JSONDecodeError as e:
        st.error(f"Error parsing quiz data: {e}")
        st.error(f"Raw response: {response_text[:500]}")
        return None
    except Exception as e:
        st.error(f"Error generating quiz: {str(e)}")
        return None

def main():
    """Main application entry point."""
    init_session_state()
    
    # Header
    st.markdown('<p class="big-font">🎓 AI Study Coach</p>', unsafe_allow_html=True)
    st.markdown("**Empowering Rural STEM Education with Multi-Agent AI**")
    st.markdown("---")
    
    # Sidebar
    with st.sidebar:
        st.title("🧭 Navigation")
        page = st.radio(
            "Choose a feature:",
            ["📚 Study Plan", "🎯 Quiz Generator", "📊 Progress Analytics", "🔍 Resource Finder"]
        )
        
        st.markdown("---")
        st.markdown("### 🔧 About This Project")
        st.info(
            "This AI Study Coach uses multiple specialized agents powered by Google Gemini "
            "to provide personalized STEM education support for rural students."
        )
        
        st.markdown("### 🎯 Technology")
        st.markdown("""
        - Google Gemini 2.0
        - Multi-Agent System
        - Firebase Backend
        - Streamlit Frontend
        """)
    
    # Main content area
    if page == "📚 Study Plan":
        st.header("📚 Personalized Study Plan Generator")
        st.markdown("Get a customized study plan based on your learning goals and available time.")
        
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
        
        if st.button("📝 Generate Study Plan", type="primary"):
            with st.spinner("Creating your personalized study plan..."):
                st.success("✅ Study plan generated successfully!")
                st.markdown("### Your Personalized Study Plan")
                
                # Mock study plan
                st.markdown(f"""
                ### {topic} Study Plan - {duration} Weeks ({level} Level)
                
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
                - 📺 Video tutorials
                - 📄 Practice worksheets
                - 🎓 Study groups
                """)
                
                # Save to history
                st.session_state.study_history.append({
                    "topic": topic,
                    "duration": duration,
                    "level": level
                })
        
        st.balloons()

        elif 'Quiz' in page:
st.header("🎯 Interactive Quiz Generator")
        st.markdown("Test your knowledge with AI-generated quizzes powered by Google Gemini.")

            # Initialize session state for quiz
    if 'quiz_data' not in st.session_state:
        st.session_state.quiz_data = None
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
        
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
        
        if st.button("🎨 Generate Quiz", type="primary"):
            if quiz_topic:
                with st.spinner("Generating quiz questions using Gemini AI..."):
                                        st.session_state.quiz_data = generate_quiz_with_gemini(quiz_topic, difficulty, num_questions)th_gemini(quiz_topic, difficulty, num_questions)
                    
                                    if st.session_state.quiz_data:        st.success("✅ Quiz generated!")
                    st.markdown(f"***Difficulty:** {st.session_state.quiz_data.get('difficulty', difficulty)}*")                        
                        # Display quiz questions
                        if 'questions' in st.session_state.quiz_data:
                            for i, q in enumerate(st.session_state.quiz_data['questions']):
                                st.markdown(f"#### Question {i+1}: {q.get('question', 'N/A')}")
                                
                                # Display options
                                options_dict = q.get('options', {})
                                user_answer = st.radio(
                                    f"Select your answer for Q{i+1}:",
                                    list(options_dict.keys()),
                                    format_func=lambda x: f"{x}) {options_dict.get(x, 'N/A')}",
                                    key=f"q_{i}"
                                )
                                                                st.session_state.user_answers[i] = user_answer
                                
                                # Show answer button
                                if st.button(f"Show Answer & Explanation", key=f"show_{i}"):
                                    correct = q.get('correct_answer', 'A')
                                    if user_answer == correct:
                                        st.success(f"✅ Correct! The answer is {correct}")
                                    else:
                                        st.error(f"❌ Incorrect. The correct answer is {correct}")
                                    
                                    st.info(f"**Explanation:** {q.get('explanation', 'N/A')}")
                                
                                st.markdown("---")
                        else:
                            st.warning("No questions generated. Please try again.")
            else:
                st.warning("⚠️ Please enter a quiz topic.")
    
    elif 'Progress' in page:
        st.header("📊 Progress Analytics")
        st.markdown("Track your learning journey and identify areas for improvement.")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Study Sessions", len(st.session_state.study_history))
        with col2:
            st.metric("Quizzes Taken", len(st.session_state.quiz_results))
        with col3:
            st.metric("Topics Covered", len(set([h['topic'] for h in st.session_state.study_history])))
        
        st.markdown("### 📈 Recent Activity")
        if st.session_state.study_history:
            for i, session in enumerate(st.session_state.study_history[-5:]):
                st.markdown(f"**Session {i+1}:** {session['topic']} - {session['level']} ({session['duration']} weeks)")
        else:
            st.info("No study sessions yet. Create your first study plan!")
        
        st.markdown("### 🎯 Learning Recommendations")
        st.markdown("""
        Based on your progress:
        - ✅ Great consistency! Keep it up
        - 📚 Try exploring more advanced topics
        - 🎯 Consider taking quizzes to test your knowledge
        - 👥 Join study groups for collaborative learning
        """)
    
    elif 'Resource' in page:
        st.header("🔍 Smart Resource Finder")
        st.markdown("Discover educational resources tailored to rural students' needs.")
        
        search_query = st.text_input(
            "What are you looking for?",
            placeholder="E.g., Free physics textbooks, online chemistry labs"
        )
        
        resource_type = st.multiselect(
            "Resource Type",
            ["Textbooks", "Video Tutorials", "Practice Problems", "Study Groups", "Online Courses"]
        )
        
        if st.button("🔍 Find Resources", type="primary"):
            with st.spinner("Searching for resources..."):
                st.success("✅ Found relevant resources!")
                
                st.markdown("### 📚 Recommended Resources")
                
                resources = [
                    {"title": "Khan Academy", "type": "Video Tutorials", "url": "https://khanacademy.org", "desc": "Free world-class education"},
                    {"title": "NCERT Books", "type": "Textbooks", "url": "https://ncert.nic.in", "desc": "Official textbooks"},
                    {"title": "PhET Simulations", "type": "Online Labs", "url": "https://phet.colorado.edu", "desc": "Interactive science simulations"},
                    {"title": "Coursera", "type": "Online Courses", "url": "https://coursera.org", "desc": "University courses online"}
                ]
                
                for resource in resources:
                    st.markdown(f"""
                    **{resource['title']}** ({resource['type']})
                    - {resource['desc']}
                    - [Visit Resource]({resource['url']})
                    ---
                    """)

if __name__ == "__main__":
    main()
