import streamlit as st
import os
import re
from dotenv import load_dotenv
from openai import OpenAI
import psutil

load_dotenv()

# --- Locate SmartStudy directory ---
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

SMARTSTUDY_DIR = find_smartstudy_path()

# --- API Key ---
api_key = st.session_state.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))
if not api_key:
    st.error("🚫 No OpenAI API key found. Please enter your API key on the homepage.")
    st.stop()

client = OpenAI(api_key=api_key)

# --- Session validation ---
if "selected_course_id" not in st.session_state or (
    "selected_content_for_revision" not in st.session_state and
    "selected_topic_for_revision" not in st.session_state
):
    st.error("Missing course or content/topic. Go back and try again.")
    st.stop()

course_id = st.session_state.selected_course_id
course_path = os.path.join(SMARTSTUDY_DIR, "revisions", course_id)
notes_folder = os.path.join(course_path, "notes")
flashcards_folder = os.path.join(course_path, "flashcards")
os.makedirs(flashcards_folder, exist_ok=True)

# --- Identify revision mode ---
is_topic_revision = "selected_topic_for_revision" in st.session_state

if is_topic_revision:
    content_name = st.session_state.selected_content
    topic_name = st.session_state.selected_topic_for_revision
    title = f"{content_name} - {topic_name}"

    note_file = os.path.join(notes_folder, f"{content_name}_{topic_name}.md")
    flashcards_file_path = os.path.join(flashcards_folder, f"{content_name}_{topic_name}.md")

    if not os.path.exists(note_file):
        st.warning("Note not found for this topic.")
        st.stop()
    with open(note_file, "r", encoding="utf-8") as f:
        all_notes = f.read()

else:
    content_name = st.session_state.selected_content_for_revision
    topic_name = None
    title = content_name
    flashcards_file_path = os.path.join(flashcards_folder, f"{content_name}.md")

    # Combine all topic-level flashcards
    topic_flashcards = []
    if os.path.exists(flashcards_folder):
        topic_files = sorted([
            f for f in os.listdir(flashcards_folder)
            if f.startswith(f"{content_name}_") and f.endswith(".md")
        ])
        for file in topic_files:
            file_path = os.path.join(flashcards_folder, file)
            with open(file_path, "r", encoding="utf-8") as f:
                topic_flashcards.append(f.read().strip())

        combined_flashcards = "\n\n".join(topic_flashcards)
        with open(flashcards_file_path, "w", encoding="utf-8") as f:
            f.write(combined_flashcards)

        all_notes = combined_flashcards
    else:
        st.warning("No topic flashcards found.")
        st.stop()

if not all_notes.strip():
    st.warning("No notes available for flashcard generation.")
    st.stop()

# --- Flashcard Display Title ---
st.markdown(f"<h2 style='text-align: left;'>🧠 Revision - {title}</h2>", unsafe_allow_html=True)

# --- Flashcard Generation Function ---
def generate_flashcards_openai(notes):
    prompt = f"""
You are a strict study assistant. Use ONLY the provided notes below to create flashcards. 
Do NOT include any extra information or examples not found in the notes.

Instructions:
- Create multiple flashcards if the content contains multiple concepts.
- Each flashcard should focus on only one concept or topic.
- Use a title for each flashcard (start with ###).
- Include only 3 to 5 short bullet points (-) per flashcard.
- Do not combine multiple topics into one flashcard.
- Be concise and clear — each flashcard should feel clean and easy to revise.
- Flashcards must include all the topics mentioned in the notes.
- Do not skip any of the points from the notes.
- If the notes include examples, include them concisely.
- If an important concept lacks clarity in the notes, you may add a **very simple example**, but only if it helps understanding and does not introduce unrelated content.

Notes:
\"\"\"{notes}\"\"\"

Now generate the flashcards in Markdown format.
"""
    response = client.chat.completions.create(
        model="gpt-4.1-nano",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

# --- Generate or Load Flashcards ---
if os.path.exists(flashcards_file_path):
    with open(flashcards_file_path, "r", encoding="utf-8") as f:
        flashcards_text = f.read().strip()
else:
    with st.spinner("Generating flashcards..."):
        flashcards_text = generate_flashcards_openai(all_notes)
        with open(flashcards_file_path, "w", encoding="utf-8") as f:
            f.write(flashcards_text)

# --- Split into individual flashcards ---
cards = re.split(r'\n(?=### )', flashcards_text)
if not cards or cards == [""]:
    st.warning("No flashcards found.")
    st.stop()

# --- Display Flashcard ---
index = st.session_state.get("flashcard_index", 0)
st.markdown(f"### 🧾 Flashcard {index + 1} of {len(cards)}")
st.markdown(cards[index], unsafe_allow_html=True)

# --- Navigation Buttons ---
col_prev, col_next = st.columns(2)
with col_prev:
    if st.button("⬅️ Previous") and index > 0:
        st.session_state.flashcard_index = index - 1
        st.rerun()
with col_next:
    if st.button("Next ➡️") and index < len(cards) - 1:
        st.session_state.flashcard_index = index + 1
        st.rerun()

st.markdown("---")

# --- Back Button ---
if st.button("🏠 Back to Content"):
    st.session_state.pop("flashcard_index", None)
    if is_topic_revision:
        st.session_state.pop("selected_topic_for_revision", None)
        st.switch_page("pages/topic_page.py")
    else:
        st.session_state.pop("selected_content_for_revision", None)
        st.switch_page("pages/course_page.py")
