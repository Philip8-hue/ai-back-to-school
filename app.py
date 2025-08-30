import os
from flask import Flask, request, render_template_string
from openai import OpenAI
import PyPDF2

app = Flask(__name__)
client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# Your HTML template and routes remain the same...

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


# Chat history
chat_history = []

# Max file size: 2 MB
MAX_FILE_SIZE = 2 * 1024 * 1024  # 2MB

# HTML template
html_form = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Back-to-School Helper</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 min-h-screen flex items-start justify-center py-10">
<div class="bg-white shadow-xl rounded-2xl p-8 w-full max-w-4xl space-y-8">

<h1 class="text-3xl font-bold text-center text-indigo-600 mb-6">🎓 AI Back-to-School Helper</h1>

<!-- Study Planner -->
<div class="border rounded-xl p-6">
<h2 class="text-xl font-semibold text-indigo-600 mb-3">📚 Personalized Study Planner</h2>
<form method="post" action="/study-plan" class="flex flex-col gap-3">
    <input type="text" name="subject" placeholder="Subject (e.g., Physics, Math)"
        class="border p-2 rounded focus:ring-2 focus:ring-indigo-400 outline-none"/>
    <input type="text" name="hours" placeholder="Hours per day"
        class="border p-2 rounded focus:ring-2 focus:ring-indigo-400 outline-none"/>
    <input type="text" name="exam_date" placeholder="Exam date (e.g., Oct 15)"
        class="border p-2 rounded focus:ring-2 focus:ring-indigo-400 outline-none"/>
    <button type="submit" class="bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 transition">
        Generate Plan
    </button>
</form>
</div>

<!-- To-Do List -->
<div class="border rounded-xl p-6">
<h2 class="text-xl font-semibold text-indigo-600 mb-3">📝 To-Do / Task Organizer</h2>
<form method="post" action="/todo" class="flex flex-col gap-3">
    <textarea name="tasks" placeholder="Enter tasks separated by commas"
        class="border p-2 rounded focus:ring-2 focus:ring-indigo-400 outline-none"></textarea>
    <button type="submit" class="bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 transition">
        Organize Tasks
    </button>
</form>
</div>

<!-- Text Summarizer -->
<div class="border rounded-xl p-6">
<h2 class="text-xl font-semibold text-indigo-600 mb-3">📄 Text/PDF Summarizer</h2>
<form method="post" action="/summarize" enctype="multipart/form-data" class="flex flex-col gap-3">
    <input type="file" name="note_file" accept=".txt,.pdf"
        class="border p-2 rounded focus:ring-2 focus:ring-indigo-400 outline-none"/>
    <button type="submit" class="bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 transition">
        Summarize
    </button>
</form>
</div>

<!-- Homework Help -->
<div class="border rounded-xl p-6">
<h2 class="text-xl font-semibold text-indigo-600 mb-3">🧮 Homework Help</h2>
<form method="post" action="/homework" class="flex flex-col gap-3">
    <input type="text" name="question" placeholder="Enter your homework question"
        class="border p-2 rounded focus:ring-2 focus:ring-indigo-400 outline-none"/>
    <button type="submit" class="bg-indigo-600 text-white py-2 rounded hover:bg-indigo-700 transition">
        Solve
    </button>
</form>
</div>

<!-- AI Responses -->
{% if chat %}
<div class="mt-6 space-y-4">
    <h2 class="text-2xl font-semibold text-gray-700">💡 AI Responses</h2>
    {% for entry in chat %}
        <div class="bg-gray-50 p-4 rounded-lg border">
            <p class="font-semibold text-gray-700">Feature:</p>
            <p class="text-gray-800">{{ entry['feature'] }}</p>
            <p class="font-semibold text-gray-700 mt-2">Your Input:</p>
            <p class="text-gray-800">{{ entry['question'] }}</p>
            <p class="font-semibold text-indigo-600 mt-2">AI Response:</p>
            <p class="text-gray-900">{{ entry['answer'] }}</p>
        </div>
    {% endfor %}
</div>
{% endif %}

</div>
</body>
</html>
"""

# Routes
@app.route("/", methods=["GET"])
def home():
    return render_template_string(html_form, chat=chat_history)

@app.route("/study-plan", methods=["POST"])
def study_plan():
    subject = request.form.get("subject")
    hours = request.form.get("hours")
    exam_date = request.form.get("exam_date")
    prompt = f"Create a personalized study plan for {subject}. The student can study {hours} hours per day until {exam_date}. Provide a daily plan."

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content
    chat_history.append({"feature": "Study Planner", "question": f"{subject}, {hours} hrs/day until {exam_date}", "answer": answer})
    return render_template_string(html_form, chat=chat_history)

@app.route("/todo", methods=["POST"])
def todo():
    tasks = request.form.get("tasks")
    prompt = f"Organize these tasks into a prioritized to-do list: {tasks}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content
    chat_history.append({"feature": "To-Do Organizer", "question": tasks, "answer": answer})
    return render_template_string(html_form, chat=chat_history)

@app.route("/summarize", methods=["POST"])
def summarize():
    if "note_file" not in request.files:
        return render_template_string(html_form, chat=chat_history)

    file = request.files["note_file"]

    # File size validation
    file.seek(0, 2)  # go to end of file
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        chat_history.append({"feature": "Text Summarizer", "question": f"{file.filename}", "answer": "Error: File too large (>2MB)."})
        return render_template_string(html_form, chat=chat_history)

    # Read text from file
    if file.filename.lower().endswith(".txt"):
        text = file.read().decode("utf-8")
    elif file.filename.lower().endswith(".pdf"):
        pdf_reader = PyPDF2.PdfReader(file)
        text = ""
        for page in pdf_reader.pages:
            text += page.extract_text() + "\n"
    else:
        chat_history.append({"feature": "Text Summarizer", "question": f"{file.filename}", "answer": "Error: Unsupported file type."})
        return render_template_string(html_form, chat=chat_history)

    prompt = f"Summarize the following text for easy studying:\n{text}"

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content
    chat_history.append({"feature": "Text Summarizer", "question": f"Uploaded file: {file.filename}", "answer": answer})
    return render_template_string(html_form, chat=chat_history)

@app.route("/homework", methods=["POST"])
def homework():
    question = request.form.get("question")
    prompt = f"Provide step-by-step help for this homework question: {question}"
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response.choices[0].message.content
    chat_history.append({"feature": "Homework Help", "question": question, "answer": answer})
    return render_template_string(html_form, chat=chat_history)


    
