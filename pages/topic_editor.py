import streamlit as st
import os
from streamlit_quill import st_quill
import psutil

# --- SmartStudy Path Setup ---
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
    return os.path.abspath("SmartStudy")  # fallback to local

SMARTSTUDY_DIR = find_smartstudy_path()

# --- Validate Session ---
if "selected_course_id" not in st.session_state or \
   "selected_content" not in st.session_state or \
   "selected_topic" not in st.session_state:
    st.error("Missing topic context. Please go back and select a topic.")
    st.stop()

# --- Extract Values ---
course_id = st.session_state.selected_course_id
content_name = st.session_state.selected_content
topic_name = st.session_state.selected_topic

# --- Note Path ---
note_dir = os.path.join(SMARTSTUDY_DIR, "revisions", course_id, "notes")
os.makedirs(note_dir, exist_ok=True)
note_file = os.path.join(note_dir, f"{content_name}_{topic_name}.md")

# --- Load Existing Note ---
existing_note = ""
if os.path.exists(note_file):
    with open(note_file, "r", encoding="utf-8") as f:
        existing_note = f.read()

# --- UI ---
st.markdown("""
    <style>
    .block-container {
        padding-top: 2rem !important;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown(f"<h2>📝 Editing: {topic_name}</h2>", unsafe_allow_html=True)

note = st_quill(value=existing_note, html=True, key="editor")

if st.button("💾 Save Note"):
    with open(note_file, "w", encoding="utf-8") as f:
        f.write(note)
    st.success("✅ Note saved successfully!")

if st.button("🔙 Go Back"):
    st.switch_page("pages/topic_page.py")
