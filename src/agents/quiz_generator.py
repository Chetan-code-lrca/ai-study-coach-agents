"""Quiz Generator Agent - Sequential Agent with PDF Tool Integration

Generates adaptive quizzes from PDF textbooks using Gemini LLM.
Demonstrates Custom Tool integration (PDF parser).
"""

import asyncio
from typing import Dict, List
from loguru import logger
import google.generativeai as genai
import PyPDF2
import io

class QuizGeneratorAgent:
    """Sequential Agent: Generates quizzes from study materials.
    
    Depends on Study Planner output. Provides input to Progress Tracker.
    Demonstrates Custom Tool integration (PDF parsing).
    """
    
    def __init__(self, gemini_api_key: str):
        self.api_key = gemini_api_key
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-1.5-pro')
        logger.info("Quiz Generator Agent initialized")
    
    async def generate_quiz_from_pdf(self, pdf_path: str, topic: str, 
                                    num_questions: int = 10) -> List[Dict]:
        """Generate quiz questions from PDF textbook.
        
        Custom Tool: PDF Parser extracts text from textbooks.
        
        Args:
            pdf_path: Path to PDF file
            topic: Specific topic to focus on
            num_questions: Number of questions to generate
        
        Returns:
            List of question dictionaries with answers
        """
        logger.info(f"Generating {num_questions} questions on {topic}")
        
        # Custom Tool: PDF Text Extraction
        pdf_text = await self._extract_pdf_text(pdf_path)
        
        # Context engineering: Limit text to relevant sections
        relevant_text = self._find_relevant_section(pdf_text, topic)
        
        # Call Gemini to generate questions
        questions = await self._generate_questions(
            relevant_text, topic, num_questions
        )
        
        logger.debug(f"Generated {len(questions)} questions")
        return questions
    
    async def _extract_pdf_text(self, pdf_path: str) -> str:
        """Custom Tool: Extract text from PDF."""
        try:
            # Simulated PDF extraction (replace with actual implementation)
            logger.debug(f"Extracting text from {pdf_path}")
            # In production, use PyPDF2 or pdfplumber
            return "Sample textbook content on thermodynamics..."
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return ""
    
    def _find_relevant_section(self, full_text: str, topic: str) -> str:
        """Context engineering: Extract topic-specific content."""
        # Simple keyword-based extraction (improve with NLP)
        lines = full_text.split('\n')
        relevant = [l for l in lines if topic.lower() in l.lower()]
        return '\n'.join(relevant[:50])  # Limit tokens
    
    async def _generate_questions(self, text: str, topic: str, 
                                 num: int) -> List[Dict]:
        """Use Gemini to generate questions."""
        prompt = f"""Based on this text about {topic}:

{text[:2000]}

Generate {num} multiple-choice questions.
Format: Question | Option A | Option B | Option C | Option D | Correct Answer

Make questions progressively harder."""
        
        response = await asyncio.to_thread(
            self.model.generate_content, prompt
        )
        
        # Parse Gemini response into structured questions
        questions = self._parse_questions(response.text)
        return questions
    
    def _parse_questions(self, gemini_output: str) -> List[Dict]:
        """Parse Gemini output into question objects."""
        questions = []
        for i, line in enumerate(gemini_output.split('\n')[:10]):
            if '|' in line:
                parts = line.split('|')
                if len(parts) >= 6:
                    questions.append({
                        'id': i + 1,
                        'question': parts[0].strip(),
                        'options': [p.strip() for p in parts[1:5]],
                        'correct': parts[5].strip(),
                        'difficulty': 'medium'
                    })
        return questions
    
    def adapt_difficulty(self, student_score: float) -> str:
        """Adaptive difficulty based on student performance."""
        if student_score < 0.5:
            return "easy"
        elif student_score < 0.75:
            return "medium"
        else:
            return "hard"

# Example usage
if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    generator = QuizGeneratorAgent(os.getenv("GEMINI_API_KEY"))
    
    quiz = asyncio.run(generator.generate_quiz_from_pdf(
        "textbook.pdf", "Thermodynamics", 10
    ))
    print(f"Generated {len(quiz)} questions")
