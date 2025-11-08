from flask import Flask, jsonify, render_template, request
from study_service import create_study_tree

app = Flask("truecopilot")

@app.route("/")
def index():
    return render_template('index.html')

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