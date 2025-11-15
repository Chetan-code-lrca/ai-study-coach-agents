"""Progress Tracker Agent - Parallel execution for progress analytics.

This agent runs in parallel to analyze student progress, identify learning gaps,
and provide actionable insights for personalized learning.
"""

import logging
from typing import Dict, List, Any
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProgressTrackerAgent:
    """Agent for tracking and analyzing student progress.
    
    Demonstrates:
    - Parallel agent execution pattern
    - Progress analytics
    - Learning gap identification
    - Data-driven insights
    """
    
    def __init__(self):
        """Initialize Progress Tracker agent."""
        self.name = "Progress Tracker"
        self.agent_type = "PARALLEL"
        logger.info(f"Initialized {self.name} Agent (Type: {self.agent_type})")
    
    async def analyze_progress(self, session_id: str, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze student progress and identify learning patterns.
        
        Args:
            session_id: Active session identifier
            user_data: User profile with historical performance data
            
        Returns:
            Progress analysis with insights and recommendations
        """
        try:
            logger.info(f"[{session_id}] Analyzing progress for user: {user_data.get('name')}")
            
            # Extract progress data
            quiz_history = user_data.get('quiz_history', [])
            study_sessions = user_data.get('study_sessions', [])
            
            # Calculate metrics
            performance_metrics = self._calculate_performance_metrics(quiz_history)
            engagement_metrics = self._calculate_engagement_metrics(study_sessions)
            learning_gaps = self._identify_learning_gaps(quiz_history)
            
            # Generate insights
            insights = self._generate_insights(
                performance_metrics,
                engagement_metrics,
                learning_gaps
            )
            
            analysis_result = {
                "session_id": session_id,
                "timestamp": datetime.now().isoformat(),
                "performance_metrics": performance_metrics,
                "engagement_metrics": engagement_metrics,
                "learning_gaps": learning_gaps,
                "insights": insights,
                "agent": self.name
            }
            
            logger.info(f"[{session_id}] Progress analysis completed. Insights: {len(insights)}")
            return analysis_result
            
        except Exception as e:
            logger.error(f"[{session_id}] Progress analysis failed: {e}")
            return {
                "session_id": session_id,
                "error": str(e),
                "agent": self.name
            }
    
    def _calculate_performance_metrics(self, quiz_history: List[Dict]) -> Dict[str, Any]:
        """Calculate performance metrics from quiz history.
        
        Args:
            quiz_history: List of past quiz attempts
            
        Returns:
            Performance metrics dictionary
        """
        if not quiz_history:
            return {
                "average_score": 0.0,
                "total_quizzes": 0,
                "improvement_rate": 0.0
            }
        
        scores = [quiz.get('score', 0) for quiz in quiz_history]
        total_quizzes = len(scores)
        average_score = sum(scores) / total_quizzes if total_quizzes > 0 else 0
        
        # Calculate improvement rate (recent vs. early performance)
        if total_quizzes >= 3:
            recent_avg = sum(scores[-3:]) / 3
            early_avg = sum(scores[:3]) / 3
            improvement_rate = ((recent_avg - early_avg) / early_avg * 100) if early_avg > 0 else 0
        else:
            improvement_rate = 0.0
        
        return {
            "average_score": round(average_score, 2),
            "total_quizzes": total_quizzes,
            "improvement_rate": round(improvement_rate, 2),
            "highest_score": max(scores) if scores else 0,
            "lowest_score": min(scores) if scores else 0
        }
    
    def _calculate_engagement_metrics(self, study_sessions: List[Dict]) -> Dict[str, Any]:
        """Calculate engagement metrics from study sessions.
        
        Args:
            study_sessions: List of study session records
            
        Returns:
            Engagement metrics dictionary
        """
        if not study_sessions:
            return {
                "total_sessions": 0,
                "total_study_time": 0,
                "average_session_duration": 0,
                "consistency_score": 0.0
            }
        
        total_sessions = len(study_sessions)
        total_study_time = sum(session.get('duration', 0) for session in study_sessions)
        average_session_duration = total_study_time / total_sessions if total_sessions > 0 else 0
        
        # Calculate consistency score (sessions per week)
        if study_sessions:
            dates = [datetime.fromisoformat(s.get('date', datetime.now().isoformat())) for s in study_sessions]
            date_range = (max(dates) - min(dates)).days + 1
            weeks = max(date_range / 7, 1)
            consistency_score = (total_sessions / weeks) * 10  # Normalized to 0-100 scale
        else:
            consistency_score = 0.0
        
        return {
            "total_sessions": total_sessions,
            "total_study_time": total_study_time,
            "average_session_duration": round(average_session_duration, 2),
            "consistency_score": min(round(consistency_score, 2), 100)  # Cap at 100
        }
    
    def _identify_learning_gaps(self, quiz_history: List[Dict]) -> List[Dict[str, Any]]:
        """Identify learning gaps from quiz performance.
        
        Args:
            quiz_history: List of past quiz attempts
            
        Returns:
            List of identified learning gaps with topics and severity
        """
        if not quiz_history:
            return []
        
        # Aggregate performance by topic
        topic_performance = {}
        for quiz in quiz_history:
            topic = quiz.get('topic', 'Unknown')
            score = quiz.get('score', 0)
            
            if topic not in topic_performance:
                topic_performance[topic] = []
            topic_performance[topic].append(score)
        
        # Identify gaps (topics with consistently low performance)
        learning_gaps = []
        for topic, scores in topic_performance.items():
            avg_score = sum(scores) / len(scores)
            
            if avg_score < 60:  # Below 60% is a gap
                severity = "high" if avg_score < 40 else "medium" if avg_score < 55 else "low"
                learning_gaps.append({
                    "topic": topic,
                    "average_score": round(avg_score, 2),
                    "attempts": len(scores),
                    "severity": severity
                })
        
        # Sort by severity and score
        learning_gaps.sort(key=lambda x: (x['severity'] == 'high', -x['average_score']), reverse=True)
        return learning_gaps
    
    def _generate_insights(self, performance: Dict, engagement: Dict, gaps: List[Dict]) -> List[str]:
        """Generate actionable insights from metrics.
        
        Args:
            performance: Performance metrics
            engagement: Engagement metrics
            gaps: Learning gaps
            
        Returns:
            List of insight strings
        """
        insights = []
        
        # Performance insights
        avg_score = performance.get('average_score', 0)
        if avg_score >= 80:
            insights.append(f"Excellent performance! Average score: {avg_score}%")
        elif avg_score >= 60:
            insights.append(f"Good progress, but room for improvement. Average score: {avg_score}%")
        else:
            insights.append(f"Performance needs attention. Average score: {avg_score}%")
        
        # Improvement tracking
        improvement = performance.get('improvement_rate', 0)
        if improvement > 10:
            insights.append(f"Great improvement trend! +{improvement}% from early attempts")
        elif improvement < -10:
            insights.append(f"Performance declining. Consider reviewing fundamentals.")
        
        # Engagement insights
        consistency = engagement.get('consistency_score', 0)
        if consistency >= 70:
            insights.append(f"Excellent study consistency! Score: {consistency}/100")
        elif consistency < 40:
            insights.append(f"Study consistency needs improvement. Try daily sessions.")
        
        # Learning gaps
        if gaps:
            high_priority_gaps = [g['topic'] for g in gaps if g['severity'] == 'high']
            if high_priority_gaps:
                insights.append(f"High priority topics: {', '.join(high_priority_gaps[:3])}")
        else:
            insights.append("No major learning gaps identified. Keep up the good work!")
        
        return insights


# Example usage
if __name__ == "__main__":
    import asyncio
    
    # Sample user data
    sample_user = {
        "name": "Rural Student",
        "quiz_history": [
            {"topic": "Physics", "score": 45, "date": "2025-01-15"},
            {"topic": "Math", "score": 78, "date": "2025-01-16"},
            {"topic": "Physics", "score": 52, "date": "2025-01-18"},
            {"topic": "Chemistry", "score": 88, "date": "2025-01-20"},
            {"topic": "Math", "score": 85, "date": "2025-01-22"},
        ],
        "study_sessions": [
            {"date": "2025-01-15T10:00:00", "duration": 45},
            {"date": "2025-01-16T14:00:00", "duration": 60},
            {"date": "2025-01-18T09:00:00", "duration": 30},
            {"date": "2025-01-20T16:00:00", "duration": 50},
        ]
    }
    
    async def test_progress_tracker():
        agent = ProgressTrackerAgent()
        result = await agent.analyze_progress("test-session-001", sample_user)
        
        print("\n=== Progress Analysis ===")
        print(f"Performance: {result['performance_metrics']}")
        print(f"Engagement: {result['engagement_metrics']}")
        print(f"Learning Gaps: {result['learning_gaps']}")
        print(f"\nInsights:")
        for insight in result['insights']:
            print(f"  - {insight}")
    
    asyncio.run(test_progress_tracker())
