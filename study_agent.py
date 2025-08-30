import os
from flask import Flask, request, jsonify
from dotenv import load_dotenv
from openai import OpenAI

# Load API key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = Flask(__name__)

@app.route("/ask", methods=["POST"])
def ask():
    data = request.json
    question = data.get("question", "")

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "system", "content": "You are a helpful study assistant."},
                  {"role": "user", "content": question}]
    )

    answer = response.choices[0].message.content
    return jsonify({"answer": answer})

if __name__ == "__main__":
    app.run(port=5001, debug=True)
