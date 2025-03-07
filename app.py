from flask import Flask, request, jsonify, render_template
import torch # type: ignore
from model import NeuralNet
from nltk_utils import bag_of_words, tokenize
import json
import random

app = Flask(__name__)

# Load intents
with open("intents.json", "r") as file:
    intents = json.load(file)

# Load trained model
data = torch.load("data.pth")

input_size = data["input_size"]
hidden_size = data["hidden_size"]
output_size = data["output_size"]
all_words = data["all_words"]
tags = data["tags"]
model_state = data["model_state"]

model = NeuralNet(input_size, hidden_size, output_size)
model.load_state_dict(model_state)
model.eval()

@app.route("/")
def home():
    return render_template("chat.html")  # Loads the web UI

@app.route("/chat", methods=["GET", "POST"])
def chat():
    if request.method == "GET":
        return "Use a POST request to send a message to the chatbot.", 405

    data = request.get_json()
    message = data.get("message", "")

    if not message:
        return jsonify({"error": "Message is required"}), 400

    sentence = tokenize(message)
    X = bag_of_words(sentence, all_words)
    X = torch.from_numpy(X).float().unsqueeze(0)

    output = model(X)
    _, predicted = torch.max(output, dim=1)
    tag = tags[predicted.item()]

    probs = torch.softmax(output, dim=1)
    prob = probs[0][predicted.item()]

    if prob.item() > 0.75:
        for intent in intents["intents"]:
            if tag == intent["tag"]:
                return jsonify({"response": random.choice(intent["responses"])})

    return jsonify({"response": "I do not understand..."})

if __name__ == "__main__":
    app.run(debug=True)
