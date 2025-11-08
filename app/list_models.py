#!/usr/bin/env python3
"""List available Gemini models."""

import os
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    print("ERROR: GEMINI_API_KEY not found!")
    exit(1)

genai.configure(api_key=api_key)

print("Available models:")
print("=" * 60)
for model in genai.list_models():
    if 'generateContent' in model.supported_generation_methods:
        print(f"  - {model.name}")

