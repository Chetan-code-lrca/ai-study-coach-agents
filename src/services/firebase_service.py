"""Firebase Service - Session and Memory management using Firebase.

Provides persistent storage for user sessions, study history, and progress data.
Demonstrates ADK Session & Memory requirements.
"""

import logging
import os
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FirebaseService:
    """Service for Firebase-based session and memory management.
    
    Demonstrates:
    - Sessions & Memory (ADK requirement)
    - Persistent data storage
    - User profile management
    - Study history tracking
    """
    
    def __init__(self, credentials_path: Optional[str] = None):
        """Initialize Firebase service.
        
        Args:
            credentials_path: Path to Firebase credentials JSON
        """
        self.credentials_path = credentials_path or os.getenv("FIREBASE_CREDENTIALS_PATH")
        
        if not self.credentials_path:
            logger.warning("No Firebase credentials. Using in-memory storage.")
            self.mock_mode = True
            self.memory_store = {}  # In-memory fallback
        else:
            self.mock_mode = False
            # In production: import firebase_admin and initialize
            logger.info("Firebase service initialized (production mode)")
    
    async def create_session(self, user_id: str, session_data: Dict[str, Any]) -> str:
        """Create a new user session.
        
        Args:
            user_id: Unique user identifier
            session_data: Initial session data
            
        Returns:
            Session ID
        """
        session_id = f"session_{user_id}_{int(datetime.now().timestamp())}"
        
        session = {
            "session_id": session_id,
            "user_id": user_id,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "data": session_data
        }
        
        if self.mock_mode:
            self.memory_store[session_id] = session
            logger.info(f"Created session (mock): {session_id}")
        else:
            # In production: Store in Firebase Firestore
            pass
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve session data.
        
        Args:
            session_id: Session identifier
            
        Returns:
            Session data dictionary or None
        """
        if self.mock_mode:
            return self.memory_store.get(session_id)
        else:
            # In production: Retrieve from Firebase
            pass
    
    async def update_session(self, session_id: str, updates: Dict[str, Any]) -> bool:
        """Update existing session data.
        
        Args:
            session_id: Session identifier
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if self.mock_mode:
                if session_id in self.memory_store:
                    self.memory_store[session_id]["data"].update(updates)
                    self.memory_store[session_id]["updated_at"] = datetime.now().isoformat()
                    logger.info(f"Updated session: {session_id}")
                    return True
                return False
            else:
                # In production: Update Firebase document
                pass
        except Exception as e:
            logger.error(f"Session update failed: {e}")
            return False
    
    async def save_user_profile(self, user_id: str, profile: Dict[str, Any]) -> bool:
        """Save or update user profile.
        
        Args:
            user_id: User identifier
            profile: User profile data
            
        Returns:
            True if successful
        """
        try:
            profile_key = f"profile_{user_id}"
            
            profile_data = {
                "user_id": user_id,
                "updated_at": datetime.now().isoformat(),
                **profile
            }
            
            if self.mock_mode:
                self.memory_store[profile_key] = profile_data
                logger.info(f"Saved user profile: {user_id}")
            else:
                # In production: Save to Firebase
                pass
            
            return True
        except Exception as e:
            logger.error(f"Profile save failed: {e}")
            return False
    
    async def get_user_profile(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve user profile.
        
        Args:
            user_id: User identifier
            
        Returns:
            User profile dictionary or None
        """
        profile_key = f"profile_{user_id}"
        
        if self.mock_mode:
            return self.memory_store.get(profile_key)
        else:
            # In production: Retrieve from Firebase
            pass
    
    async def save_study_record(self, user_id: str, record: Dict[str, Any]) -> bool:
        """Save a study session record.
        
        Args:
            user_id: User identifier
            record: Study record data
            
        Returns:
            True if successful
        """
        try:
            record_key = f"study_{user_id}_{int(datetime.now().timestamp())}"
            
            study_data = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                **record
            }
            
            if self.mock_mode:
                self.memory_store[record_key] = study_data
                logger.info(f"Saved study record: {record_key}")
            else:
                # In production: Save to Firebase
                pass
            
            return True
        except Exception as e:
            logger.error(f"Study record save failed: {e}")
            return False
    
    async def get_study_history(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Retrieve user's study history.
        
        Args:
            user_id: User identifier
            limit: Maximum number of records to return
            
        Returns:
            List of study records
        """
        if self.mock_mode:
            # Filter records for this user
            records = [
                v for k, v in self.memory_store.items()
                if k.startswith(f"study_{user_id}")
            ]
            # Sort by timestamp (newest first)
            records.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return records[:limit]
        else:
            # In production: Query Firebase collection
            pass
    
    async def save_quiz_result(self, user_id: str, quiz_data: Dict[str, Any]) -> bool:
        """Save quiz results.
        
        Args:
            user_id: User identifier
            quiz_data: Quiz results and metadata
            
        Returns:
            True if successful
        """
        try:
            quiz_key = f"quiz_{user_id}_{int(datetime.now().timestamp())}"
            
            quiz_record = {
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                **quiz_data
            }
            
            if self.mock_mode:
                self.memory_store[quiz_key] = quiz_record
                logger.info(f"Saved quiz result: {quiz_key}")
            else:
                # In production: Save to Firebase
                pass
            
            return True
        except Exception as e:
            logger.error(f"Quiz save failed: {e}")
            return False
    
    async def get_quiz_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Retrieve user's quiz history.
        
        Args:
            user_id: User identifier
            
        Returns:
            List of quiz results
        """
        if self.mock_mode:
            records = [
                v for k, v in self.memory_store.items()
                if k.startswith(f"quiz_{user_id}")
            ]
            records.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
            return records
        else:
            # In production: Query Firebase
            pass


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_firebase_service():
        service = FirebaseService()
        
        user_id = "student_001"
        
        # Test 1: Create session
        print("\n=== Test 1: Create Session ===")
        session_id = await service.create_session(
            user_id,
            {"topic": "Physics", "level": "intermediate"}
        )
        print(f"Created session: {session_id}")
        
        # Test 2: Save user profile
        print("\n=== Test 2: Save User Profile ===")
        profile = {
            "name": "Rural Student",
            "grade": 10,
            "subjects": ["Physics", "Math", "Chemistry"],
            "learning_goals": ["Improve physics understanding", "Score 90%+"]
        }
        success = await service.save_user_profile(user_id, profile)
        print(f"Profile saved: {success}")
        
        # Test 3: Save study record
        print("\n=== Test 3: Save Study Record ===")
        study_record = {
            "topic": "Newton's Laws",
            "duration": 45,
            "activities": ["video", "practice"]
        }
        await service.save_study_record(user_id, study_record)
        
        # Test 4: Save quiz result
        print("\n=== Test 4: Save Quiz Result ===")
        quiz_data = {
            "topic": "Motion",
            "score": 85,
            "total_questions": 10,
            "correct_answers": 8.5
        }
        await service.save_quiz_result(user_id, quiz_data)
        
        # Test 5: Retrieve data
        print("\n=== Test 5: Retrieve Data ===")
        retrieved_profile = await service.get_user_profile(user_id)
        print(f"Profile: {retrieved_profile['name']}")
        
        study_history = await service.get_study_history(user_id)
        print(f"Study records: {len(study_history)}")
        
        quiz_history = await service.get_quiz_history(user_id)
        print(f"Quiz results: {len(quiz_history)}")
    
    asyncio.run(test_firebase_service())
