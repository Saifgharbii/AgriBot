from flask import Flask, request, jsonify ,render_template
import os
import json
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
from werkzeug.utils import secure_filename

# Flask App Initialization
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'conversations.json'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def load_conversations():
    """Loads the JSON database of conversations."""
    if not os.path.exists(app.config['DATABASE']):
        with open(app.config['DATABASE'], 'w') as f:
            json.dump({}, f)
    with open(app.config['DATABASE'], 'r') as f:
        return json.load(f)

def save_conversations(conversations):
    """Saves the updated conversations to the JSON file."""
    with open(app.config['DATABASE'], 'w') as f:
        json.dump(conversations, f, indent=4)

# Initialize the model
generation_config = {
    "temperature": 0.7,
    "top_p": 0.95,
    "top_k": 40,
    "max_output_tokens": 8192,
    "response_mime_type": "text/plain",
}

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config,
)

from flask import Flask, render_template, request, jsonify



@app.route('/')
def home():
    return render_template('index.html')  # Ensure you have 'index.html' in a 'templates' folder


@app.route('/upload_image', methods=['POST'])
def upload_image():
    """Handles image uploads and returns the local path."""
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    return jsonify({"message": "File uploaded successfully", "file_path": filepath})

@app.route('/send_message', methods=['POST'])
def send_message():
    """Handles sending a message to the chatbot and saving conversation history."""
    data = request.json
    user_id = str(data.get("user_id"))  # Identify user session
    user_message = data.get("message")
    image_path = data.get("image_path")  # Optional image

    if not user_message:
        return jsonify({"error": "Message cannot be empty"}), 400

    conversations = load_conversations()
    user_history = conversations.get(user_id, [])

    # Upload image to Gemini if provided
    files = []
    if image_path and os.path.exists(image_path):
        files.append(genai.upload_file(image_path))

    # Start a new chat session with history
    chat_session = model.start_chat(history=user_history)
    response = chat_session.send_message(user_message)
    bot_reply = response.text

    # Save conversation
    user_history.append({"role": "user", "message": user_message})
    user_history.append({"role": "bot", "message": bot_reply})
    conversations[user_id] = user_history
    save_conversations(conversations)

    return jsonify({"response": bot_reply, "history": user_history})

@app.route('/get_conversations', methods=['GET'])
def get_conversations():
    """Returns the conversation history of a user."""
    user_id = request.args.get("user_id")
    if not user_id:
        return jsonify({"error": "User ID required"}), 400
    conversations = load_conversations()
    return jsonify({"history": conversations.get(user_id, [])})

if __name__ == '__main__':
    app.run(debug=True)
