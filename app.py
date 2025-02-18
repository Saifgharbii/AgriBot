from flask import Flask, request, jsonify ,render_template ,send_from_directory
import os
import json
import google.generativeai as genai
from google.ai.generativelanguage_v1beta.types import content
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

# Flask App Initialization
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['DATABASE'] = 'conversations.json'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Configure Gemini API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def load_conversations() -> dict :
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

SYSEM_INSTRUCTION = """You are AgriBot, a highly intelligent and specialized AI assistant designed to help farmers and agricultural professionals optimize their work. Your main responsibilities include:

Plant Disease Diagnosis 🌿🔬

Analyze uploaded photos of plants.
Detect diseases, nutrient deficiencies, or pest infestations.
Provide precise diagnoses with explanations.
Suggest treatment solutions, including organic and chemical remedies.
General Agricultural Assistance 🚜🌾

Answer farming-related questions (soil health, irrigation, fertilization, pest control).
Provide best practices for different crops and climates.
Guide users on sustainable farming techniques.
Smart and Professional Communication 🗣️🤖

Be clear, concise, and professional in responses.
Use easy-to-understand language for farmers of all expertise levels.
Provide scientific insights in a user-friendly way.
Example Interaction:

👨‍🌾 User: "My tomato leaves have yellow spots. What should I do?"
🤖 AgriBot:
"Based on your photo, your tomato plant may have early blight (Alternaria solani), a common fungal disease. I recommend:
✅ Removing infected leaves.
✅ Applying a copper-based fungicide.
✅ Ensuring good air circulation to prevent moisture buildup.
Let me know if you need organic alternatives! """

model = genai.GenerativeModel(
    model_name="gemini-2.0-flash-exp",
    generation_config=generation_config,
    system_instruction= SYSEM_INSTRUCTION,
)
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/chat-bot')
def chat_bot():
    return render_template('index.html')  # Serve the frontend

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
    
    return jsonify({"message": "File uploaded successfully", "file_path": filename})

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
    new_image = None
    if image_path and os.path.exists(image_path):
        new_image = genai.upload_file(image_path)
        files.append(new_image)
    print(user_history)
    # Start a new chat session with history
    chat_session = model.start_chat(history=user_history)
    response = chat_session.send_message(content = [user_message, new_image] if new_image else user_message)
    bot_reply = response.text


    # Save conversation
    user_history.append({"role": "user", "parts": [user_message] })
    user_history.append({"role": "model", "parts": [bot_reply]})
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

UPLOAD_FOLDER = os.path.join(os.getcwd(), "uploads")

@app.route('/uploads/<filename>')
def get_image(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
