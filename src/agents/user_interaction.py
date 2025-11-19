"""User Interaction Agent for AI Study Coach.

Handles all user interactions including:
- Processing user input and queries
- Providing conversational responses  
- Collecting user preferences and feedback
- Managing user sessions and context
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime


class UserInteractionAgent:
    """Manages user interactions and communication."""
    
    def __init__(self, user_id: str = None):
        self.user_id = user_id
        self.session_context = {}
        self.interaction_history = []
        self.user_preferences = {}
        self.logger = logging.getLogger(__name__)
        
    def process_user_input(self, user_input: str, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """Process and interpret user input."""
        try:
            processed_input = {
                'raw_input': user_input,
                'timestamp': datetime.now().isoformat(),
                'user_id': self.user_id,
                'context': context or {},
                'intent': self._detect_intent(user_input),
                'entities': self._extract_entities(user_input)
            }
            self.interaction_history.append(processed_input)
            self.logger.info(f"Processed input: {processed_input['intent']}")
            return processed_input
        except Exception as e:
            self.logger.error(f"Error processing input: {str(e)}")
            return {'error': str(e)}
    
    def generate_response(self, query_result: Dict[str, Any], tone: str = 'friendly') -> str:
        """Generate conversational response."""
        try:
            if 'error' in query_result:
                return self._format_error_response(query_result['error'])
            return self._format_response(query_result, tone)
        except Exception as e:
            self.logger.error(f"Error generating response: {str(e)}")
            return "I apologize, but I encountered an error. Please try again."
    
    def collect_feedback(self, feedback: Dict[str, Any]) -> bool:
        """Collect user feedback."""
        try:
            feedback['timestamp'] = datetime.now().isoformat()
            feedback['user_id'] = self.user_id
            self.logger.info(f"Feedback collected: {feedback}")
            return True
        except Exception as e:
            self.logger.error(f"Error collecting feedback: {str(e)}")
            return False
    
    def update_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Update user preferences."""
        try:
            self.user_preferences.update(preferences)
            self.logger.info(f"Updated preferences for user {self.user_id}")
            return True
        except Exception as e:
            self.logger.error(f"Error updating preferences: {str(e)}")
            return False
    
    def get_context(self) -> Dict[str, Any]:
        """Get current session context."""
        return {
            'user_id': self.user_id,
            'session_context': self.session_context,
            'preferences': self.user_preferences,
            'interaction_count': len(self.interaction_history)
        }
    
    def _detect_intent(self, user_input: str) -> str:
        """Detect user intent from input."""
        user_input_lower = user_input.lower()
        if any(word in user_input_lower for word in ['help', 'assist', 'guide']):
            return 'help_request'
        elif any(word in user_input_lower for word in ['quiz', 'test', 'exam']):
            return 'quiz_request'
        elif any(word in user_input_lower for word in ['resource', 'material', 'recommend']):
            return 'resource_request'
        elif any(word in user_input_lower for word in ['progress', 'status', 'achievement']):
            return 'progress_check'
        elif any(word in user_input_lower for word in ['plan', 'schedule', 'study']):
            return 'planning_request'
        else:
            return 'general_query'
    
    def _extract_entities(self, user_input: str) -> List[str]:
        """Extract relevant entities from input."""
        entities = []
        keywords = ['math', 'science', 'history', 'english', 'programming', 
                   'python', 'java', 'chemistry', 'physics', 'biology']
        for keyword in keywords:
            if keyword in user_input.lower():
                entities.append(keyword)
        return entities
    
    def _format_response(self, result: Dict[str, Any], tone: str) -> str:
        """Format response based on tone."""
        if tone == 'friendly':
            prefix = "Great question! "
        elif tone == 'professional':
            prefix = "Based on your query: "
        else:
            prefix = ""
        return prefix + str(result.get('message', 'Here is your result.'))
    
    def _format_error_response(self, error: str) -> str:
        """Format error messages in user-friendly way."""
        return f"I apologize, but something went wrong: {error}. Please try again."
