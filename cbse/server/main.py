from flask import Flask, send_file, request, jsonify
from flask_cors import CORS
import asyncio
import os
from google import genai
import edge_tts

# Flask app
app = Flask(__name__)
CORS(app)

# Gemini API client
client = genai.Client(api_key="AIzaSyBc70X28NtqrbzEpkz6uKcbLfXgDZ1Sixs")

# Folder to store audio
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
AUDIO_FILE = os.path.join(UPLOAD_FOLDER, "latest.mp3")


# ---------- TEXT GENERATION FUNCTIONS ----------
def generate_feynman(name, topic, class_, board):
    """Generate a simplified explanation using Feynman Technique."""
    prompt = (
        f"Student Name: {name}\n"
        f"Topic: {topic}\n"
        f"Class: {class_}\n"
        f"Board: {board}\n\n"
        f"Explain {topic} to {name} in a short, clear, simple, and detailed way "
        f"for a Class {class_} student following the {board} board. "
        f"Use the Feynman Technique: break down the idea into basic terms, avoid jargon, "
        f"use analogies or examples, and relate it to everyday experiences. "
        f"Make sure it's easy to understand for their level."
    )
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )
    return response.text.strip()


def generate_explanation(name, class_, topic, board):
    """Generate detailed HTML-friendly explanation."""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=(
            f"Explain the topic {topic} of class {class_} to a student named {name} "
            f"as per syllabus of {board} elaborately. "
            f"When giving your output wherever there is a new line insert a <br> there "
            f"and if there is HTML related content, write it like this: &lt;tagname&gt;. "
            f"Don't mention about this in your prompt."
        )
    )
    return response.text


# ---------- AUDIO GENERATION FUNCTION ----------
async def text_to_speech(text, output_path):
    """Convert text to speech and save as MP3."""
    voice = "en-GB-RyanNeural"
    communicate = edge_tts.Communicate(text=text, voice=voice)
    await communicate.save(output_path)


# ---------- ROUTES ----------
@app.route("/generate_audio", methods=["POST"])
def generate_audio_post():
    """Generate Feynman explanation from JSON POST and return audio file."""
    data = request.get_json()
    name = data.get("name")
    topic = data.get("topic")
    class_ = data.get("class")
    board = data.get("board")

    if not all([name, topic, class_, board]):
        return jsonify({"error": "Missing required fields"}), 400

    explanation = generate_feynman(name, topic, class_, board).replace("\n", " ").replace("*", "")
    asyncio.run(text_to_speech(explanation, AUDIO_FILE))

    if os.path.exists(AUDIO_FILE):
        return send_file(AUDIO_FILE, mimetype="audio/mpeg")

    return jsonify({"error": "Audio generation failed"}), 500


@app.route("/audio")
def get_audio():
    """Serve the latest audio file."""
    if os.path.exists(AUDIO_FILE):
        return send_file(AUDIO_FILE, mimetype="audio/mpeg")
    return "No audio found", 404


@app.route("/generate", methods=["POST"])
def generate():
    """Generate a detailed HTML-friendly explanation."""
    data = request.get_json()
    name = data.get("name")
    topic = data.get("topic")
    board = data.get("board")
    class_ = data.get("class")

    explanation = generate_explanation(name, class_, topic, board)
    return jsonify({"txt": explanation})


# ---------- RUN SERVER ----------
if __name__ == "__main__":
    print("Flask server running at http://127.0.0.1:5000")
    app.run(debug=True)
