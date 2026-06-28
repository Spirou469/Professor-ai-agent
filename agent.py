from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import requests

app = Flask(__name__)
CORS(app, origins="*")

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
MODEL = "mistralai/mistral-7b-instruct:free"

AGENT_INFO = {
    "name": "Professor AI",
    "version": "1.0.0",
    "description": "Your personal AI teacher. Ask me anything about any subject.",
    "price_usdc": 2.0,
    "capabilities": ["Explain any subject", "Create exercises", "Generate study plans", "Multilingual support"],
    "languages": ["English", "French", "Spanish", "Arabic", "Portuguese", "Swahili"],
    "author": "Spirou469",
    "github": "https://github.com/Spirou469/Professor-ai-agent"
}

SYSTEM_PROMPT = """You are Professor AI, the world's best personal tutor.
- Use simple clear language adapted to the student
- Give concrete examples and analogies
- Break complex concepts into small steps
- Respond in the same language the student uses
- End with a quick summary and one practice question"""

def ask_ai(prompt):
    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://professor-ai-agent.onrender.com",
            "X-Title": "Professor AI"
        },
        json={
            "model": MODEL,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt}
            ]
        }
    )
    data = response.json()
    if "choices" in data:
        return data["choices"][0]["message"]["content"]
    elif "error" in data:
        return f"Erreur API: {data['error']['message']}"
    else:
        return f"Réponse inattendue: {str(data)}"
@app.route("/", methods=["GET"])
def home():
    return jsonify({"status": "active", "agent": AGENT_INFO})

@app.route("/info", methods=["GET"])
def info():
    return jsonify(AGENT_INFO)

@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "healthy", "agent": "Professor AI"})

@app.route("/teach", methods=["POST", "OPTIONS"])
def teach():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    try:
        data = request.get_json(force=True)
        if not data or "question" not in data:
            return jsonify({"error": "Please provide a question"}), 400
        question = data.get("question", "")
        level = data.get("level", "intermediate")
        subject = data.get("subject", "general")
        prompt = f"Student level: {level}\nSubject: {subject}\nQuestion: {question}"
        answer = ask_ai(prompt)
        return jsonify({
            "status": "success",
            "agent": "Professor AI",
            "question": question,
            "answer": answer,
            "price_paid_usdc": 2.0
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/exercise", methods=["POST", "OPTIONS"])
def generate_exercise():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    try:
        data = request.get_json(force=True)
        subject = data.get("subject", "mathematics")
        level = data.get("level", "intermediate")
        count = min(data.get("count", 3), 5)
        prompt = f"Create {count} practice exercises for {subject} at {level} level with answers."
        answer = ask_ai(prompt)
        return jsonify({"status": "success", "exercises": answer, "price_paid_usdc": 2.0})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/study-plan", methods=["POST", "OPTIONS"])
def study_plan():
    if request.method == "OPTIONS":
        return jsonify({}), 200
    try:
        data = request.get_json(force=True)
        subject = data.get("subject", "")
        goal = data.get("goal", "")
        weeks = data.get("duration_weeks", 4)
        prompt = f"Create a {weeks}-week study plan for {subject}. Goal: {goal}."
        answer = ask_ai(prompt)
        return jsonify({"status": "success", "study_plan": answer, "price_paid_usdc": 2.0})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
