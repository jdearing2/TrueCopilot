import os
import json
import re
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.api_core import exceptions
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
# Using gemini-2.5-flash for better rate limits and faster responses
model = genai.GenerativeModel('gemini-2.5-flash')


def call_with_retry(func, *args, max_retries=3, base_delay=1, max_delay=60, request_type="API", **kwargs):
    """
    Call a function with retry logic and exponential backoff for rate limits.
    Logs all API requests and responses for monitoring.
    
    Args:
        func: Function to call
        *args: Positional arguments for func
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds for exponential backoff
        max_delay: Maximum delay in seconds
        request_type: Type of request for logging (e.g., "Subtopics", "Questions")
        **kwargs: Keyword arguments for func
        
    Returns:
        Result of func call
    """
    last_exception = None
    request_start = time.time()
    
    for attempt in range(max_retries + 1):
        try:
            print(f"[API REQUEST] {request_type} - Attempt {attempt + 1}/{max_retries + 1}")
            print(f"[API REQUEST] {request_type} - Making API call to Gemini...")
            
            result = func(*args, **kwargs)
            
            request_duration = time.time() - request_start
            print(f"[API SUCCESS] {request_type} - Request completed in {request_duration:.2f}s")
            
            # Log response info if available
            if hasattr(result, 'text'):
                response_length = len(result.text) if result.text else 0
                print(f"[API SUCCESS] {request_type} - Response length: {response_length} characters")
            
            return result
            
        except exceptions.ResourceExhausted as e:
            last_exception = e
            request_duration = time.time() - request_start
            
            # Parse rate limit details from error
            error_str = str(e)
            print(f"[API RATE LIMIT] {request_type} - Rate limit hit after {request_duration:.2f}s")
            print(f"[API RATE LIMIT] {request_type} - Error details: {error_str[:200]}")
            
            # Try to extract quota information
            if 'quota' in error_str.lower():
                quota_match = re.search(r'limit:\s*(\d+)', error_str, re.IGNORECASE)
                if quota_match:
                    print(f"[API RATE LIMIT] {request_type} - Quota limit: {quota_match.group(1)} requests")
            
            # Try to extract retry delay
            delay_match = re.search(r'retry in ([\d.]+)s?', error_str, re.IGNORECASE)
            if delay_match:
                suggested_delay = float(delay_match.group(1))
                print(f"[API RATE LIMIT] {request_type} - API suggests retry in {suggested_delay:.1f}s")
            
            if attempt < max_retries:
                # Extract retry delay from error if available
                delay = base_delay * (2 ** attempt)
                
                if delay_match:
                    delay = float(delay_match.group(1)) + 1  # Add 1 second buffer
                
                delay = min(delay, max_delay)
                print(f"[API RATE LIMIT] {request_type} - Waiting {delay:.1f}s before retry (attempt {attempt + 1}/{max_retries})...")
                time.sleep(delay)
                request_start = time.time()  # Reset timer for retry
            else:
                print(f"[API ERROR] {request_type} - Max retries ({max_retries}) exceeded for rate limit")
                print(f"[API ERROR] {request_type} - Final error: {e}")
                raise
                
        except Exception as e:
            request_duration = time.time() - request_start
            print(f"[API ERROR] {request_type} - Request failed after {request_duration:.2f}s")
            print(f"[API ERROR] {request_type} - Error type: {type(e).__name__}")
            print(f"[API ERROR] {request_type} - Error message: {str(e)[:300]}")
            raise
    
    if last_exception:
        raise last_exception


def get_subtopics(topic: str) -> list[str]:
    """
    Generate sub topics for a given topic using Gemini API.
    
    Args:
        topic: The main topic to study
        
    Returns:
        List of sub topic strings
    """
    prompt = f"""Generate EXACTLY 9 specific, concrete sub topics for studying "{topic}".

Requirements:
- Each sub topic must be SPECIFIC to "{topic}" (not generic like "Basics", "Advanced", "Introduction", "Overview")
- Each sub topic should be a distinct, important area or concept within "{topic}"
- Return EXACTLY 9 sub topics (one for each planet)

Return ONLY a valid JSON array of strings. No other text, no markdown.
Format: ["Sub topic 1", "Sub topic 2", "Sub topic 3", "Sub topic 4", "Sub topic 5", "Sub topic 6", "Sub topic 7", "Sub topic 8", "Sub topic 9"]

Sub topics for "{topic}":"""

    try:
        response = call_with_retry(model.generate_content, prompt, request_type="Subtopics")
        text = response.text.strip()
        print(f"[API RESPONSE] Subtopics - Raw response preview: {text[:100]}...")
        
        # Improved JSON extraction - similar to generate_questions
        if text.startswith('```'):
            parts = text.split('```')
            for part in parts:
                part = part.strip()
                if part.startswith('json'):
                    text = part[4:].strip()
                    break
                elif part.startswith('['):
                    text = part
                    break
        else:
            # Try to find JSON array in the text
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                text = json_match.group(0)
        
        text = text.strip()
        
        # Remove any leading/trailing non-JSON characters
        if not text.startswith('['):
            # Try to find the array
            start_idx = text.find('[')
            end_idx = text.rfind(']')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                text = text[start_idx:end_idx+1]
        
        # Parse JSON
        subtopics = json.loads(text)
        if isinstance(subtopics, list) and len(subtopics) > 0:
            # Filter out generic subtopics
            filtered = []
            generic_patterns = [
                r'\b(basics?|basic)\b',
                r'\b(advanced|advanced concepts?)\b',
                r'\b(introduction|intro)\b',
                r'\b(overview)\b',
                r'\b(applications?)\b',
                r'\b(general concepts?)\b'
            ]
            
            for st in subtopics:
                st_str = str(st).strip()
                st_lower = st_str.lower()
                
                # Check if it matches generic patterns
                is_generic = False
                for pattern in generic_patterns:
                    if re.search(pattern, st_lower):
                        # If it's just "{topic} Basics" or similar, it's generic
                        # But allow longer phrases like "Advanced Machine Learning Techniques"
                        words = st_lower.split()
                        if len(words) <= 3 and any(re.search(pattern, word) for word in words):
                            is_generic = True
                            break
                
                # Also check if it's too generic (just topic name + generic word)
                if not is_generic:
                    topic_lower = topic.lower()
                    if st_lower.startswith(topic_lower) and len(st_lower.split()) <= 3:
                        # Might be generic, check further
                        remaining = st_lower[len(topic_lower):].strip()
                        if remaining in ['basics', 'basic', 'advanced', 'introduction', 'overview', 'applications']:
                            is_generic = True
                
                if not is_generic:
                    filtered.append(st_str)
            
            # We need exactly 9 subtopics for 9 planets
            if len(filtered) >= 9:
                print(f"Successfully generated {len(filtered)} specific sub topics: {filtered[:9]}")
                return filtered[:9]  # Take first 9
            elif len(filtered) > 0:
                # If we have some but not 9, pad with originals or request more
                print(f"Warning: Only {len(filtered)} sub topics passed filtering. Using available: {filtered}")
                # Try to fill from original list if needed
                remaining = [str(st) for st in subtopics if str(st).strip() not in filtered]
                while len(filtered) < 9 and remaining:
                    filtered.append(remaining.pop(0))
                return filtered[:9] if len(filtered) >= 9 else filtered
            else:
                print(f"Warning: All sub topics were filtered as generic. Using original list: {subtopics}")
                return [str(st) for st in subtopics][:9]
        else:
            print(f"Warning: Invalid response format. Got: {text[:200]}")
            return []
    except json.JSONDecodeError as e:
        print(f"JSON decode error generating sub topics: {e}")
        print(f"Response text: {text[:500] if 'text' in locals() else 'N/A'}")
        # Try one more time with a simpler prompt
        try:
            retry_prompt = f'Return a JSON array of 5 specific sub topics for "{topic}". Example: ["Topic 1", "Topic 2", "Topic 3", "Topic 4", "Topic 5"]'
            retry_response = call_with_retry(model.generate_content, retry_prompt, max_retries=2, request_type="Subtopics-Retry")
            retry_text = retry_response.text.strip()
            # Extract JSON
            json_match = re.search(r'\[.*\]', retry_text, re.DOTALL)
            if json_match:
                retry_text = json_match.group(0)
            subtopics = json.loads(retry_text)
            if isinstance(subtopics, list) and len(subtopics) > 0:
                return [str(st) for st in subtopics]
        except:
            pass
        return []
    except Exception as e:
        print(f"Error generating sub topics: {e}")
        print(f"Response text: {text[:500] if 'text' in locals() else 'N/A'}")
        return []


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
    prompt = f"""Generate {num_questions} multiple choice questions about "{subtopic}" (topic: "{topic}").

Return ONLY a JSON array. Each question structure:
{{
    "question": "Question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_index": 0,
    "explanation": "Brief explanation"
}}

Questions for "{subtopic}":"""

    try:
        response = call_with_retry(model.generate_content, prompt, request_type=f"Questions-{subtopic[:30]}")
        text = response.text.strip()
        print(f"[API RESPONSE] Questions for '{subtopic}' - Raw response preview: {text[:100]}...")
        
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
    
    Uses parallel processing to generate questions for multiple subtopics simultaneously,
    which significantly speeds up the generation process.
    
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
    start_time = time.time()
    print(f"[{time.strftime('%H:%M:%S')}] Starting study tree generation for topic: '{topic}'")
    
    # Step 1: Get sub topics (exactly 9 for 9 planets)
    print(f"[{time.strftime('%H:%M:%S')}] Step 1/2: Generating 9 subtopics (one per planet)...")
    subtopics_list = get_subtopics(topic)
    # Ensure we have exactly 9
    if len(subtopics_list) < 9:
        print(f"[{time.strftime('%H:%M:%S')}] ⚠ Warning: Only {len(subtopics_list)} subtopics generated, expected 9")
    elif len(subtopics_list) > 9:
        subtopics_list = subtopics_list[:9]
        print(f"[{time.strftime('%H:%M:%S')}] ✓ Using first 9 subtopics")
    else:
        print(f"[{time.strftime('%H:%M:%S')}] ✓ Generated exactly 9 subtopics")
    
    if not subtopics_list:
        print(f"[{time.strftime('%H:%M:%S')}] ⚠ No subtopics generated. Returning empty tree.")
        return {
            "topic": topic,
            "subtopics": []
        }
    
    # Step 2: Generate questions for each sub topic in parallel
    print(f"[{time.strftime('%H:%M:%S')}] Step 2/2: Generating questions for {len(subtopics_list)} subtopics (parallel)...")
    print(f"[{time.strftime('%H:%M:%S')}] [API] Will make {len(subtopics_list)} parallel API calls (max 6 concurrent)...")
    
    # Create a list to store results in order
    subtopics_with_questions = [None] * len(subtopics_list)
    
    # Use ThreadPoolExecutor to generate questions in parallel
    # Limit to 6 concurrent requests to maximize parallelism
    with ThreadPoolExecutor(max_workers=6) as executor:
        print(f"[{time.strftime('%H:%M:%S')}] [API] ThreadPoolExecutor initialized with max_workers=6")
        # Submit all tasks
        future_to_subtopic = {
            executor.submit(generate_questions, subtopic, topic, questions_per_subtopic): (original_idx, subtopic)
            for original_idx, subtopic in enumerate(subtopics_list)
        }
        
        # Process completed tasks as they finish
        completed = 0
        for future in as_completed(future_to_subtopic):
            original_idx, subtopic = future_to_subtopic[future]
            completed += 1
            
            try:
                print(f"[{time.strftime('%H:%M:%S')}] [API] Processing completed request {completed}/{len(subtopics_list)} for: '{subtopic}'")
                questions = future.result()
                subtopics_with_questions[original_idx] = {
                    "name": subtopic,
                    "questions": questions
                }
                print(f"[{time.strftime('%H:%M:%S')}] ✓ ({completed}/{len(subtopics_list)}) Completed: '{subtopic}' - {len(questions)} questions")
            except Exception as e:
                print(f"[{time.strftime('%H:%M:%S')}] ✗ [API ERROR] Error generating questions for '{subtopic}': {type(e).__name__}: {e}")
                subtopics_with_questions[original_idx] = {
                    "name": subtopic,
                    "questions": []
                }
    
    # Filter out None values (shouldn't happen, but safety check)
    subtopics_with_questions = [st for st in subtopics_with_questions if st is not None]
    
    elapsed_time = time.time() - start_time
    total_api_calls = 1 + len(subtopics_list)  # 1 for subtopics + 1 per subtopic for questions
    print(f"[{time.strftime('%H:%M:%S')}] ========================================")
    print(f"[{time.strftime('%H:%M:%S')}] ✓ Study tree generation complete!")
    print(f"[{time.strftime('%H:%M:%S')}]   Total time: {elapsed_time:.1f} seconds")
    print(f"[{time.strftime('%H:%M:%S')}]   Total API calls made: {total_api_calls}")
    print(f"[{time.strftime('%H:%M:%S')}]   Average time per API call: {elapsed_time/total_api_calls:.2f}s")
    print(f"[{time.strftime('%H:%M:%S')}] ========================================")
    
    return {
        "topic": topic,
        "subtopics": subtopics_with_questions
    }

