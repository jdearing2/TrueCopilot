from flask import Flask, jsonify

app = Flask("truecopilot")

@app.route("/")
def index():
    return jsonify({"message": "TrueCopilot running."}), 200