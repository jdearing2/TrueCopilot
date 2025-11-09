from flask import Flask, jsonify, render_template, request, send_from_directory, Response
from study_service import create_study_tree, generate_planet_transition_message
from tts_service import text_to_speech
import os

app = Flask("truecopilot", static_folder=None)

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/audio/<filename>")
def serve_audio(filename):
    """Serve audio files from the audio directory."""
    audio_dir = os.path.join(os.path.dirname(__file__), 'audio')
    return send_from_directory(audio_dir, filename)

@app.route("/api/generate-study", methods=["POST"])
def generate_study():
    """Generate a study tree for a given topic."""
    try:
        data = request.get_json()
        topic = data.get('topic', '').strip()
        questions_per_subtopic = data.get('questions_per_subtopic', 3)
        
        if not topic:
            return jsonify({"error": "Topic is required"}), 400
        
        # Validate questions_per_subtopic
        try:
            questions_per_subtopic = int(questions_per_subtopic)
            if questions_per_subtopic < 1 or questions_per_subtopic > 10:
                questions_per_subtopic = 3
        except (ValueError, TypeError):
            questions_per_subtopic = 3
        
        # Generate the study tree
        study_tree = create_study_tree(topic, questions_per_subtopic)
        
        return jsonify(study_tree), 200
        
    except Exception as e:
        print(f"Error generating study tree: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/tts", methods=["POST"])
def tts():
    """Convert text to speech using ElevenLabs."""
    try:
        data = request.get_json()
        text = data.get('text', '').strip()
        
        if not text:
            return jsonify({"error": "Text is required"}), 400
        
        # Generate speech
        audio_data = text_to_speech(text)
        
        # Return audio as MP3
        return Response(
            audio_data,
            mimetype='audio/mpeg',
            headers={
                'Content-Disposition': 'inline; filename=speech.mp3',
                'Cache-Control': 'no-cache'
            }
        )
        
    except ValueError as e:
        print(f"TTS configuration error: {e}")
        return jsonify({"error": "TTS service not configured"}), 500
    except Exception as e:
        print(f"Error generating TTS: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/api/planet-transition", methods=["POST"])
def planet_transition():
    """Generate a quirky transition message between planets."""
    try:
        data = request.get_json()
        topic = data.get('topic', '').strip()
        from_planet = data.get('from_planet', '').strip()
        to_planet = data.get('to_planet', '').strip()
        from_subtopic = data.get('from_subtopic', '').strip()
        to_subtopic = data.get('to_subtopic', '').strip()
        
        if not all([topic, from_planet, to_planet, from_subtopic, to_subtopic]):
            return jsonify({"error": "All fields are required"}), 400
        
        message = generate_planet_transition_message(topic, from_planet, to_planet, from_subtopic, to_subtopic)
        return jsonify({"message": message}), 200
        
    except Exception as e:
        print(f"Error generating transition message: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()
