import os
import json
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-pro')


def get_subtopics(topic: str) -> list[str]:
    """
    Generate sub topics for a given topic using Gemini API.
    
    Args:
        topic: The main topic to study
        
    Returns:
        List of sub topic strings
    """
    prompt = f"""Generate 4-6 important sub topics for studying "{topic}". 
Return ONLY a JSON array of strings, no other text. Each sub topic should be a key area within {topic}.
Example format: ["Sub topic 1", "Sub topic 2", "Sub topic 3"]

Sub topics for "{topic}":"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up the response - remove markdown code blocks if present
        if text.startswith('```'):
            text = text.split('```')[1]
            if text.startswith('json'):
                text = text[4:]
        text = text.strip()
        
        # Parse JSON
        subtopics = json.loads(text)
        if isinstance(subtopics, list):
            return [str(st) for st in subtopics]
        return []
    except Exception as e:
        print(f"Error generating sub topics: {e}")
        # Fallback to generic sub topics
        return [f"{topic} Basics", f"{topic} Advanced Concepts", f"{topic} Applications"]


def generate_questions(subtopic: str, topic: str, num_questions: int = 3) -> list[dict]:
    """
    Generate multiple choice questions for a sub topic.
    
    Args:
        subtopic: The sub topic to generate questions for
        topic: The main topic (for context)
        num_questions: Number of questions to generate (default: 3)
        
    Returns:
        List of question dictionaries with structure:
        {
            "question": str,
            "options": [str, str, str, str],
            "correct_index": int,
            "explanation": str
        }
    """
    prompt = f"""Generate {num_questions} multiple choice questions about "{subtopic}" (within the broader topic of "{topic}").

For each question, provide:
1. A clear, specific question
2. Four answer choices (A, B, C, D)
3. The correct answer (specify which letter)
4. A brief explanation of why that answer is correct

Return ONLY a JSON array. Each question should have this exact structure:
{{
    "question": "The question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 0,
    "explanation": "Explanation of why the correct answer is right"
}}

Generate questions for "{subtopic}":"""

    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        
        # Clean up the response - remove markdown code blocks if present
        if text.startswith('```'):
            parts = text.split('```')
            for part in parts:
                if part.strip().startswith('json') or part.strip().startswith('{') or part.strip().startswith('['):
                    text = part.strip()
                    if text.startswith('json'):
                        text = text[4:].strip()
                    break
        
        text = text.strip()
        
        # Parse JSON
        questions = json.loads(text)
        if isinstance(questions, list):
            # Validate and clean questions
            validated_questions = []
            for q in questions:
                if isinstance(q, dict) and 'question' in q and 'options' in q:
                    # Ensure correct_index is valid
                    if 'correct_index' not in q or not isinstance(q['correct_index'], int):
                        q['correct_index'] = 0
                    if q['correct_index'] < 0 or q['correct_index'] >= len(q.get('options', [])):
                        q['correct_index'] = 0
                    if 'explanation' not in q:
                        q['explanation'] = "This is the correct answer."
                    validated_questions.append(q)
            return validated_questions
        return []
    except Exception as e:
        print(f"Error generating questions for {subtopic}: {e}")
        print(f"Response text: {text[:500] if 'text' in locals() else 'N/A'}")
        return []


def create_study_tree(topic: str, questions_per_subtopic: int = 3) -> dict:
    """
    Create a complete study tree structure for a topic.
    
    Args:
        topic: The main topic to study
        questions_per_subtopic: Number of questions to generate per sub topic
        
    Returns:
        Dictionary with structure:
        {
            "topic": str,
            "subtopics": [
                {
                    "name": str,
                    "questions": [
                        {
                            "question": str,
                            "options": [str, str, str, str],
                            "correct_index": int,
                            "explanation": str
                        }
                    ]
                }
            ]
        }
    """
    print(f"Generating study tree for topic: {topic}")
    
    # Step 1: Get sub topics
    subtopics_list = get_subtopics(topic)
    print(f"Generated {len(subtopics_list)} sub topics")
    
    # Step 2: Generate questions for each sub topic
    subtopics_with_questions = []
    for subtopic in subtopics_list:
        print(f"Generating questions for: {subtopic}")
        questions = generate_questions(subtopic, topic, questions_per_subtopic)
        subtopics_with_questions.append({
            "name": subtopic,
            "questions": questions
        })
    
    return {
        "topic": topic,
        "subtopics": subtopics_with_questions
    }

