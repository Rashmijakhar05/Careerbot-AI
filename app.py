from flask import Flask, render_template, request, jsonify, session, redirect
import google.generativeai as genai
import PyPDF2
import os
from dotenv import load_dotenv

# =========================
# ENV LOAD
# =========================
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

# =========================
# GEMINI SETUP
# =========================
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-flash-latest")

# =========================
# MEMORY (temporary)
# =========================
chat_history = {}

# =========================
# HOME
# =========================
@app.route("/")
def home():
    if "user" not in session:
        return render_template("login.html")
    return render_template("index.html")

# =========================
# LOGIN
# =========================
@app.route("/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username", "").strip()

    # ❌ empty username check
    if not username:
        return jsonify({
            "status": "error",
            "message": "Username is required"
        })

    session["user"] = username

    if username not in chat_history:
        chat_history[username] = []

    return jsonify({"status": "success"})
# =========================
# LOGOUT
# =========================
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")

# =========================
# CHATBOT
# =========================
@app.route("/chat", methods=["POST"])
def chat():
    try:
        user = session.get("user", "guest")
        user_message = request.json["message"]

        prompt = f"""
You are an Expert AI Career Assistant.

Help user in:
- DSA concepts
- Resume building
- Interview preparation
- AI/ML basics
- Job guidance

Be clear, structured, and helpful.

User question:
{user_message}
"""

        response = model.generate_content(prompt)
        reply = response.text

        # Save chat
        chat_history.setdefault(user, []).append({
            "user": user_message,
            "bot": reply
        })

        return jsonify({
            "reply": reply,
            "history": chat_history[user]
        })

    except Exception as e:
        return jsonify({"reply": f"⚠️ AI Error: {str(e)}"})

# =========================
# RESUME ANALYZER
# =========================
@app.route("/upload", methods=["POST"])
def upload_resume():
    try:
        file = request.files["file"]

        pdf_reader = PyPDF2.PdfReader(file)

        text = ""
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text

        if not text.strip():
            return jsonify({"result": "⚠️ No readable text found in PDF"})

        prompt = f"""
You are an ATS Resume Analyzer.

Analyze the resume and give:

1. ATS Score (0-100)
2. Strengths
3. Missing Skills
4. Recommended Roles
5. Improvement Suggestions

Be strict and realistic.

Resume:
{text}
"""

        response = model.generate_content(prompt)
        result = response.text

        return jsonify({"result": result})

    except Exception as e:
        return jsonify({"result": f"⚠️ Resume Error: {str(e)}"})

# =========================
# CLEAR CHAT
# =========================
@app.route("/clear", methods=["POST"])
def clear_chat():
    user = session.get("user")
    if user in chat_history:
        chat_history[user] = []
    return jsonify({"status": "cleared"})

# =========================
# RUN APP
# =========================
if __name__ == "__main__":
    app.run(debug=True)