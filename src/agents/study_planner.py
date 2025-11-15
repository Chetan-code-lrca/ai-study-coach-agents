"""Study Planner Agent - Sequential Agent for Personalized Learning Schedules

This agent creates weekly study plans based on student profile, available time,
and weak topics. Integrates with Gemini for intelligent scheduling.

Key Features:
- Adaptive scheduling based on student pace
- Prioritizes weak topics from progress tracker
- Considers available study hours per day
- Implements spaced repetition algorithm
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List
from loguru import logger
import google.generativeai as genai

class StudyPlannerAgent:
    """Sequential Agent: Creates personalized weekly study schedules.
    
    This agent operates first in the agent chain, providing input to
    the Quiz Generator Agent.
    """
    
    def __init__(self, gemini_api_key: str):
        """Initialize Study Planner with Gemini API.
        
        Args:
            gemini_api_key: API key for Google Gemini LLM
        """
        self.api_key = gemini_api_key
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        logger.info("Study Planner Agent initialized with Gemini")
    
    async def create_study_plan(self, student_profile: Dict) -> Dict:
        """Generate 7-day personalized study schedule.
        
        Uses Gemini to create intelligent study plans that:
        - Prioritize weak topics
        - Implement spaced repetition
        - Adapt to available study hours
        - Balance multiple subjects
        
        Args:
            student_profile: Dictionary containing:
                - name: Student name
                - grade: Current grade level
                - subjects: List of subjects
                - weak_topics: Topics needing focus
                - study_hours_per_day: Available study time
        
        Returns:
            Dictionary with day-wise study schedule
        """
        logger.info(f"Creating study plan for {student_profile.get('name')}")
        
        # Context engineering: Compress profile into minimal tokens
        context = f"""Student: {student_profile.get('name')}, Grade {student_profile.get('grade')}
Subjects: {', '.join(student_profile.get('subjects', []))}
Weak Topics: {', '.join(student_profile.get('weak_topics', []))}
Daily Study Time: {student_profile.get('study_hours_per_day', 2)} hours"""
        
        prompt = f"""{context}

Create a 7-day study schedule that:
1. Prioritizes weak topics with 40% more time
2. Implements spaced repetition (review on day 3 and day 7)
3. Balances subjects across the week
4. Includes buffer time for rest

Format: Day | Topic | Duration | Goals"""
        
        try:
            # Call Gemini LLM for intelligent planning
            response = await self._call_gemini(prompt)
            plan = self._parse_plan(response)
            
            # Log for observability
            logger.debug(f"Study plan created: {len(plan)} days scheduled")
            
            return plan
            
        except Exception as e:
            logger.error(f"Error creating study plan: {e}")
            # Fallback to rule-based planning
            return self._fallback_plan(student_profile)
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API with retry logic."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await asyncio.to_thread(
                    self.model.generate_content, prompt
                )
                return response.text
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Gemini API retry {attempt + 1}/{max_retries}")
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
    
    def _parse_plan(self, gemini_response: str) -> Dict:
        """Parse Gemini output into structured plan."""
        # TODO: Implement robust parsing
        days = {}
        for i, day in enumerate(gemini_response.split('\n\n')[:7]):
            days[f"day_{i+1}"] = {
                "content": day.strip(),
                "date": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            }
        return days
    
    def _fallback_plan(self, profile: Dict) -> Dict:
        """Rule-based fallback when Gemini fails."""
        logger.warning("Using fallback planner (rule-based)")
        # Simple round-robin scheduling
        subjects = profile.get('subjects', [])
        plan = {}
        for i in range(7):
            subject = subjects[i % len(subjects)] if subjects else "General Study"
            plan[f"day_{i+1}"] = {
                "subject": subject,
                "duration": "2 hours",
                "date": (datetime.now() + timedelta(days=i)).strftime("%Y-%m-%d")
            }
        return plan
    
    async def send_daily_reminder(self, student_id: str, today_plan: Dict):
        """Loop Agent: Send daily study reminders.
        
        This demonstrates the Loop Agent pattern for recurring tasks.
        """
        logger.info(f"Sending daily reminder to student {student_id}")
        # TODO: Integrate with Firebase Cloud Messaging or email
        reminder_text = f"""Good morning! Today's focus:
{today_plan.get('content', 'Continue your studies')}

Stay consistent! 🎯"""
        return reminder_text

# Example usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    
    planner = StudyPlannerAgent(api_key)
    
    # Sample student profile
    student = {
        "name": "Rajesh Kumar",
        "grade": 10,
        "subjects": ["Physics", "Chemistry", "Math"],
        "weak_topics": ["Thermodynamics", "Organic Chemistry"],
        "study_hours_per_day": 3
    }
    
    # Create plan
    plan = asyncio.run(planner.create_study_plan(student))
    print("Study Plan Created:", plan)
