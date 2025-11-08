#!/usr/bin/env python3
"""
Test script to debug Gemini API queries for subtopic generation.
"""

import os
import json
import re
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

# Configure Gemini API
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("ERROR: GEMINI_API_KEY not found in environment!")
    print("Please set it in a .env file or environment variable.")
    exit(1)

print(f"API Key found: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else '***'}")
genai.configure(api_key=api_key)
# Using gemini-2.5-flash for better rate limits and faster responses
model = genai.GenerativeModel('gemini-2.5-flash')

def test_get_subtopics(topic: str):
    """Test the get_subtopics function with detailed debugging."""
    print(f"\n{'='*60}")
    print(f"Testing subtopic generation for: '{topic}'")
    print(f"{'='*60}\n")
    
    prompt = f"""You are an expert educator. Generate 4-6 specific, concrete sub topics for studying "{topic}".

CRITICAL REQUIREMENTS:
- Each sub topic must be SPECIFIC and CONCRETE to "{topic}"
- DO NOT use generic terms like "Basics", "Advanced Concepts", "Introduction", "Overview", "Applications"
- Each sub topic should be a distinct, important area or concept within "{topic}"
- Return EXACTLY 4-6 sub topics (prefer 5-6 if possible)

Examples of GOOD sub topics:
- For "Python": ["Lists and List Comprehensions", "Dictionary Operations", "Function Definitions and Scope", "Object-Oriented Programming", "File I/O Operations"]
- For "World War II": ["The Battle of Normandy (D-Day)", "The Battle of Stalingrad", "The Pacific Theater Strategy", "The Holocaust", "The Atomic Bombings"]
- For "Photosynthesis": ["Light-Dependent Reactions", "The Calvin Cycle", "Chlorophyll and Pigments", "C3 vs C4 Pathways", "Factors Affecting Photosynthesis Rate"]

Examples of BAD sub topics (DO NOT USE):
- "{topic} Basics", "{topic} Advanced", "Introduction to {topic}", "{topic} Overview"

Return ONLY a valid JSON array of strings. No other text, no explanations, no markdown formatting.
Format: ["Sub topic 1", "Sub topic 2", "Sub topic 3", "Sub topic 4", "Sub topic 5"]

Sub topics for "{topic}":"""

    print("PROMPT SENT TO API:")
    print("-" * 60)
    print(prompt)
    print("-" * 60)
    print("\nCalling Gemini API...\n")
    
    try:
        response = model.generate_content(prompt)
        
        print("RAW API RESPONSE:")
        print("-" * 60)
        print(f"Type: {type(response)}")
        print(f"Response object: {response}")
        print("-" * 60)
        
        # Get the text
        if hasattr(response, 'text'):
            text = response.text
        elif hasattr(response, 'candidates') and len(response.candidates) > 0:
            if hasattr(response.candidates[0], 'content'):
                text = response.candidates[0].content.parts[0].text
            else:
                text = str(response.candidates[0])
        else:
            text = str(response)
        
        print(f"\nRESPONSE TEXT (raw):")
        print("-" * 60)
        print(repr(text))
        print("-" * 60)
        
        print(f"\nRESPONSE TEXT (formatted):")
        print("-" * 60)
        print(text)
        print("-" * 60)
        
        # Now try to parse it
        print(f"\nPARSING ATTEMPT:")
        print("-" * 60)
        
        original_text = text.strip()
        text = original_text
        
        # Step 1: Check for markdown code blocks
        print(f"1. Original text length: {len(text)}")
        print(f"   Starts with ```: {text.startswith('```')}")
        
        if text.startswith('```'):
            parts = text.split('```')
            print(f"   Found {len(parts)} parts after splitting by ```")
            for i, part in enumerate(parts):
                part = part.strip()
                print(f"   Part {i}: {repr(part[:50])}...")
                if part.startswith('json'):
                    text = part[4:].strip()
                    print(f"   → Using part {i} (after removing 'json'): {repr(text[:50])}...")
                    break
                elif part.startswith('['):
                    text = part
                    print(f"   → Using part {i} (starts with '['): {repr(text[:50])}...")
                    break
        else:
            # Try to find JSON array in the text
            json_match = re.search(r'\[.*\]', text, re.DOTALL)
            if json_match:
                text = json_match.group(0)
                print(f"   → Found JSON array via regex: {repr(text[:50])}...")
            else:
                print(f"   → No JSON array found via regex")
        
        text = text.strip()
        print(f"2. After initial cleanup: {repr(text[:100])}...")
        
        # Remove any leading/trailing non-JSON characters
        if not text.startswith('['):
            start_idx = text.find('[')
            end_idx = text.rfind(']')
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                text = text[start_idx:end_idx+1]
                print(f"3. Extracted JSON from text: {repr(text[:100])}...")
        
        print(f"4. Final text to parse: {repr(text)}")
        
        # Try to parse
        try:
            subtopics = json.loads(text)
            print(f"\n✅ SUCCESS! Parsed JSON:")
            print(f"   Type: {type(subtopics)}")
            print(f"   Length: {len(subtopics) if isinstance(subtopics, list) else 'N/A'}")
            print(f"   Content: {subtopics}")
            
            if isinstance(subtopics, list):
                print(f"\n📋 SUBTOPICS ({len(subtopics)}):")
                for i, st in enumerate(subtopics, 1):
                    print(f"   {i}. {st}")
                return subtopics
            else:
                print(f"\n❌ ERROR: Response is not a list!")
                return []
                
        except json.JSONDecodeError as e:
            print(f"\n❌ JSON DECODE ERROR:")
            print(f"   Error: {e}")
            print(f"   Text that failed: {repr(text)}")
            return []
            
    except Exception as e:
        print(f"\n❌ EXCEPTION:")
        print(f"   Type: {type(e).__name__}")
        print(f"   Error: {e}")
        import traceback
        traceback.print_exc()
        return []


if __name__ == "__main__":
    import sys
    
    # Get topic from command line or use default
    if len(sys.argv) > 1:
        topic = " ".join(sys.argv[1:])
    else:
        topic = "Python"  # Default test topic
    
    print("=" * 60)
    print("GEMINI API TEST - SUBTOPIC GENERATION")
    print("=" * 60)
    
    result = test_get_subtopics(topic)
    print(f"\n✅ Final result for '{topic}': {result}\n")

