import streamlit as st
import os
import random
import json
import hashlib
from dotenv import load_dotenv
from openai import OpenAI
import psutil

# --- Helper: Locate SmartStudy directory ---
def find_smartstudy_path():
    for part in psutil.disk_partitions():
        if part.device.startswith("C:"):
            continue
        try:
            base = os.path.join(part.device, "SmartStudy")
            os.makedirs(base, exist_ok=True)
            return base
        except:
            continue
    return os.path.abspath("SmartStudy")

# --- Setup ---
load_dotenv()
SMARTSTUDY_DIR = find_smartstudy_path()
api_key = st.session_state.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))

if not api_key:
    st.error("🚫 No OpenAI API key found. Please enter your API key above.")
    st.stop()

client = OpenAI(api_key=api_key)

# --- Session Validation ---
if "selected_course_id" not in st.session_state or "selected_content_for_quiz" not in st.session_state:
    st.error("Missing course or content. Please go back and try again.")
    st.stop()

# --- Paths ---
course_id = st.session_state.selected_course_id
content_name = st.session_state.selected_content_for_quiz
course_path = os.path.join(SMARTSTUDY_DIR, "revisions", course_id)
flashcards_folder = os.path.join(course_path, "flashcards")
quiz_folder = os.path.join(course_path, "quiz")
os.makedirs(quiz_folder, exist_ok=True)

# --- Resolve Flashcard Path ---
flashcard_file = os.path.join(flashcards_folder, f"{content_name}.md")
if not os.path.exists(flashcard_file):
    # Try matching a topic-level flashcard starting with content_name_
    topic_candidates = [
        os.path.join(flashcards_folder, f)
        for f in os.listdir(flashcards_folder)
        if f.startswith(f"{content_name}_") and f.endswith(".md")
    ]
    if topic_candidates:
        # Combine them into content-level flashcard
        topic_flashcards = []
        for file in sorted(topic_candidates):
            with open(file, "r", encoding="utf-8") as f:
                topic_flashcards.append(f.read().strip())

        combined = "\n\n".join(topic_flashcards)
        with open(flashcard_file, "w", encoding="utf-8") as f:
            f.write(combined)
    else:
        st.error("❌ Flashcards not found for this content.")
        st.stop()

# --- Read flashcards ---
with open(flashcard_file, "r", encoding="utf-8") as f:
    flashcard_data = f.read()

# --- Hash for change detection ---
content_hash = hashlib.md5(flashcard_data.encode("utf-8")).hexdigest()
quiz_file = os.path.join(quiz_folder, f"{content_name}.json")
quiz_hash_file = os.path.join(quiz_folder, f"{content_name}_hash.txt")

# --- Generate Quiz from Flashcards ---
def generate_quiz_from_flashcards(flashcards):
    prompt = f"""
You are a helpful assistant. Use ONLY the notes below to create quiz questions.

Instructions:
- Generate AS MANY **multiple-choice questions** (MCQs) as needed to fully cover all the key concepts and bullet points from the notes.
- Each question must have 4 options.
- Highlight the correct option clearly in the JSON response.
- Do NOT add any content that is not present in the notes.
- Do NOT skip any point from the flashcards.
- Avoid repeating the same concept across questions.

Notes:
\"\"\"{flashcards}\"\"\"

Format:
[
  {{
    "question": "What is ...?",
    "options": ["A", "B", "C", "D"],
    "answer": "B"
  }},
  ...
]
"""
    res = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return json.loads(res.choices[0].message.content)

st.markdown("""
    <style>
    /* Remove top padding Streamlit adds */
    .block-container {
        padding-top: 3rem !important;
    }
    </style>
""", unsafe_allow_html=True)

if st.button("← Back", key="back_button"):
    st.switch_page("pages/course_page.py")  # Adjust to the actual page you're returning to

# --- Load or Refresh Quiz ---
if (
    not os.path.exists(quiz_file)
    or not os.path.exists(quiz_hash_file)
    or open(quiz_hash_file).read().strip() != content_hash
):
    with st.spinner("Generating quiz from updated flashcards..."):
        quiz_data = generate_quiz_from_flashcards(flashcard_data)
        with open(quiz_file, "w", encoding="utf-8") as f:
            json.dump(quiz_data, f, indent=2)
        with open(quiz_hash_file, "w") as f:
            f.write(content_hash)
else:
    with open(quiz_file, "r", encoding="utf-8") as f:
        quiz_data = json.load(f)

# --- Session Setup ---
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = random.sample(quiz_data, len(quiz_data))
    st.session_state.current_question_index = 0
    st.session_state.score = 0
    st.session_state.show_answer = False
    st.session_state.selected_option = None

# --- Display Quiz ---
current_index = st.session_state.current_question_index
current_question = st.session_state.quiz_questions[current_index]

st.markdown(f"### ❓ Question {current_index + 1} of {len(quiz_data)}")
st.write(current_question["question"])

# --- Answer Options ---
options = current_question["options"]
selected_index = (
    options.index(st.session_state.selected_option)
    if st.session_state.get("selected_option") in options
    else 0
)
selected_option = st.radio(
    "Choose an option:",
    options,
    index=selected_index,
    key=f"radio_{current_index}"
)

# --- Buttons ---
col1, col2 = st.columns(2)
with col1:
    if st.button("✅ Submit"):
        st.session_state.selected_option = selected_option
        st.session_state.show_answer = True
        if selected_option == current_question["answer"]:
            st.session_state.score += 1
with col2:
    if st.button("❌ Show Answer"):
        st.session_state.show_answer = True

# --- Show Answer ---
if st.session_state.show_answer:
    st.markdown("### 🧾 Answer Review:")
    for opt in options:
        if opt == current_question["answer"]:
            st.markdown(f"- ✅ **{opt}**", unsafe_allow_html=True)
        elif opt == st.session_state.selected_option:
            st.markdown(f"- ❌ <span style='color:red;'>{opt}</span>", unsafe_allow_html=True)
        else:
            st.markdown(f"- {opt}", unsafe_allow_html=True)

# --- Navigation ---
if current_index + 1 < len(st.session_state.quiz_questions):
    if st.button("➡️ Next Question"):
        st.session_state.current_question_index += 1
        st.session_state.selected_option = None
        st.session_state.show_answer = False
        st.rerun()
else:
    st.success(f"🎉 Quiz Complete! Your Score: {st.session_state.score} / {len(quiz_data)}")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🔁 Restart Quiz"):
            for key in ["quiz_questions", "current_question_index", "score", "selected_option", "show_answer"]:
                st.session_state.pop(key, None)
            st.rerun()
    with col2:
        if st.button("🏠 Back to Course"):
            st.session_state.pop("selected_content_for_quiz", None)
            st.switch_page("pages/course_page.py")
