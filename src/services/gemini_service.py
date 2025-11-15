"""Gemini Service - Centralized wrapper for Google Gemini API integration.

Provides a unified interface for all agents to interact with Google's Gemini LLM,
including error handling, retry logic, and response formatting.
"""

import logging
import os
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from tenacity import retry, stop_after_attempt, wait_exponential

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiService:
    """Centralized service for Gemini API interactions.
    
    Demonstrates:
    - Gemini LLM integration (core ADK requirement)
    - Error handling and retry logic
    - Response formatting and validation
    - Context management for efficient token usage
    """
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-2.0-flash-exp"):
        """Initialize Gemini service.
        
        Args:
            api_key: Google API key (defaults to environment variable)
            model_name: Gemini model to use
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name
        
        if not self.api_key:
            logger.warning("No Gemini API key provided. Service will use mock mode.")
            self.mock_mode = True
        else:
            self.mock_mode = False
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(model_name)
            logger.info(f"Initialized Gemini Service with model: {model_name}")
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_text(self, prompt: str, temperature: float = 0.7, 
                          max_tokens: int = 1024) -> Dict[str, Any]:
        """Generate text using Gemini with retry logic.
        
        Args:
            prompt: Input prompt for generation
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Returns:
            Dictionary with generated text and metadata
        """
        try:
            if self.mock_mode:
                return self._generate_mock_response(prompt)
            
            logger.info(f"Generating text with Gemini (temp={temperature}, max_tokens={max_tokens})")
            
            generation_config = {
                "temperature": temperature,
                "max_output_tokens": max_tokens,
            }
            
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config
            )
            
            return {
                "text": response.text,
                "model": self.model_name,
                "prompt_tokens": len(prompt.split()),  # Approximate
                "completion_tokens": len(response.text.split()),  # Approximate
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Gemini generation failed: {e}")
            return {
                "text": "",
                "error": str(e),
                "success": False
            }
    
    async def generate_structured_output(self, prompt: str, 
                                        output_format: str = "json") -> Dict[str, Any]:
        """Generate structured output (JSON, bullet points, etc.).
        
        Args:
            prompt: Input prompt
            output_format: Desired output format (json, bullets, numbered)
            
        Returns:
            Structured response dictionary
        """
        format_instructions = {
            "json": "Respond ONLY with valid JSON. No additional text.",
            "bullets": "Respond with bullet points using - prefix.",
            "numbered": "Respond with numbered list format."
        }
        
        instruction = format_instructions.get(output_format, "")
        enhanced_prompt = f"{prompt}\n\n{instruction}"
        
        return await self.generate_text(enhanced_prompt, temperature=0.3)
    
    async def chat(self, messages: List[Dict[str, str]], 
                  temperature: float = 0.7) -> Dict[str, Any]:
        """Multi-turn chat interaction with Gemini.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            temperature: Sampling temperature
            
        Returns:
            Response dictionary with assistant's reply
        """
        try:
            if self.mock_mode:
                return self._generate_mock_response(messages[-1]['content'])
            
            # Convert messages to Gemini chat format
            chat = self.model.start_chat(history=[])
            
            # Process message history
            for msg in messages[:-1]:
                if msg['role'] == 'user':
                    chat.send_message(msg['content'])
            
            # Send final message
            response = chat.send_message(
                messages[-1]['content'],
                generation_config={"temperature": temperature}
            )
            
            return {
                "text": response.text,
                "model": self.model_name,
                "success": True
            }
            
        except Exception as e:
            logger.error(f"Gemini chat failed: {e}")
            return {
                "text": "",
                "error": str(e),
                "success": False
            }
    
    def _generate_mock_response(self, prompt: str) -> Dict[str, Any]:
        """Generate mock response when API key is not available.
        
        Args:
            prompt: Input prompt
            
        Returns:
            Mock response dictionary
        """
        logger.info("Using mock Gemini response")
        
        # Generate contextual mock based on prompt keywords
        if "study plan" in prompt.lower() or "schedule" in prompt.lower():
            mock_text = """Here's a personalized study plan:
            
            Week 1-2: Foundation Building
            - Review basic concepts (30 min/day)
            - Complete practice problems (45 min/day)
            - Watch educational videos (20 min/day)
            
            Week 3-4: Deep Dive
            - Advanced topics (1 hour/day)
            - Group study sessions (2x per week)
            - Mock quizzes (1x per week)
            
            Focus areas based on your learning gaps: Physics mechanics, Algebra fundamentals.
            """
        
        elif "quiz" in prompt.lower() or "questions" in prompt.lower():
            mock_text = """Quiz Questions:
            
            1. What is Newton's First Law of Motion?
            A) Force equals mass times acceleration
            B) An object at rest stays at rest unless acted upon
            C) For every action, there is an equal reaction
            D) Energy is conserved
            
            2. Calculate the velocity of an object with 10J kinetic energy and 2kg mass.
            A) 2.5 m/s
            B) 3.16 m/s
            C) 5 m/s
            D) 10 m/s
            """
        
        else:
            mock_text = f"Mock response to: {prompt[:100]}...\n\nThis is a demonstration response showing how Gemini would process this request."
        
        return {
            "text": mock_text,
            "model": f"{self.model_name} (mock)",
            "prompt_tokens": len(prompt.split()),
            "completion_tokens": len(mock_text.split()),
            "success": True,
            "mock": True
        }
    
    def optimize_prompt(self, base_prompt: str, context: Dict[str, Any]) -> str:
        """Optimize prompt with context for efficient token usage.
        
        Demonstrates context engineering for ADK requirements.
        
        Args:
            base_prompt: Base prompt template
            context: Context dictionary with user data
            
        Returns:
            Optimized prompt string
        """
        # Extract relevant context
        user_level = context.get('level', 'beginner')
        topic = context.get('topic', 'general')
        goals = context.get('goals', [])
        
        # Build compact context
        context_str = f"Student Level: {user_level}\nTopic: {topic}"
        if goals:
            context_str += f"\nGoals: {', '.join(goals[:3])}"  # Limit to 3 goals
        
        # Combine with base prompt
        optimized = f"{context_str}\n\n{base_prompt}"
        
        logger.info(f"Optimized prompt: {len(optimized)} characters")
        return optimized


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def test_gemini_service():
        # Initialize service (will use mock mode if no API key)
        service = GeminiService()
        
        # Test 1: Simple generation
        print("\n=== Test 1: Simple Generation ===")
        result = await service.generate_text(
            "Explain Newton's Laws of Motion in simple terms for a high school student."
        )
        print(f"Success: {result['success']}")
        print(f"Model: {result['model']}")
        print(f"Response: {result['text'][:200]}...")
        
        # Test 2: Structured output
        print("\n=== Test 2: Structured Output ===")
        result = await service.generate_structured_output(
            "List 5 key physics concepts for STEM students",
            output_format="bullets"
        )
        print(f"Response:\n{result['text']}")
        
        # Test 3: Chat interaction
        print("\n=== Test 3: Chat Interaction ===")
        messages = [
            {"role": "user", "content": "I'm struggling with physics homework."},
            {"role": "assistant", "content": "I can help! What topic are you working on?"},
            {"role": "user", "content": "Projectile motion problems."}
        ]
        result = await service.chat(messages)
        print(f"Response: {result['text'][:200]}...")
        
        # Test 4: Prompt optimization
        print("\n=== Test 4: Prompt Optimization ===")
        context = {
            "level": "intermediate",
            "topic": "Thermodynamics",
            "goals": ["understand heat transfer", "solve problems", "ace exam"]
        }
        optimized = service.optimize_prompt(
            "Create a study plan for this student.",
            context
        )
        print(f"Optimized prompt:\n{optimized}")
    
    asyncio.run(test_gemini_service())
