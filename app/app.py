from flask import Flask, jsonify, render_template

app = Flask("truecopilot")

@app.route("/")
def index():
    return render_template('index.html')