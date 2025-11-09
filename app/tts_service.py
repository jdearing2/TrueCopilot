import os
import requests
from dotenv import load_dotenv

# Load .env from project root
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=env_path)

ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY')
# Using a free tier compatible voice ID
# Rachel - clear, friendly female voice (free tier compatible)
ELEVENLABS_VOICE_ID = "21m00Tcm4TlvDq8ikWAM"
ELEVENLABS_API_URL = f"https://api.elevenlabs.io/v1/text-to-speech/{ELEVENLABS_VOICE_ID}"

def text_to_speech(text: str) -> bytes:
    """
    Convert text to speech using ElevenLabs API.
    
    Args:
        text: Text to convert to speech
        
    Returns:
        Audio data as bytes (MP3 format)
        
    Raises:
        ValueError: If API key is not found
        requests.exceptions.RequestException: If API request fails
    """
    if not ELEVENLABS_API_KEY:
        raise ValueError("ELEVENLABS_API_KEY not found in environment")
    
    headers = {
        "Accept": "audio/mpeg",
        "Content-Type": "application/json",
        "xi-api-key": ELEVENLABS_API_KEY
    }
    
    data = {
        "text": text,
        "model_id": "eleven_turbo_v2",  # Free tier compatible model
        "voice_settings": {
            "stability": 0.5,
            "similarity_boost": 0.75
        }
    }
    
    try:
        print(f"[TTS] Generating speech for text: {text[:50]}...")
        response = requests.post(ELEVENLABS_API_URL, json=data, headers=headers, timeout=30)
        response.raise_for_status()
        print(f"[TTS] Successfully generated audio ({len(response.content)} bytes)")
        return response.content
    except requests.exceptions.RequestException as e:
        print(f"[TTS ERROR] ElevenLabs API error: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[TTS ERROR] Response status: {e.response.status_code}")
            print(f"[TTS ERROR] Response text: {e.response.text[:500]}")
        raise

