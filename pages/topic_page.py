import streamlit as st
import os
import json
from streamlit_quill import st_quill
import psutil

# --- Locate preferred drive for SmartStudy storage ---
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
    return os.path.abspath("SmartStudy")  # fallback

SMARTSTUDY_DIR = find_smartstudy_path()

# Validate session
if "selected_course_id" not in st.session_state or "selected_content" not in st.session_state:
    st.error("No module selected. Go back and select a content.")
    st.stop()

course_id = st.session_state.selected_course_id
course_name = st.session_state.selected_course_name
content_name = st.session_state.selected_content

# ✅ Use SmartStudy base path
course_path = os.path.join(SMARTSTUDY_DIR, "revisions", course_id)
topic_dir = os.path.join(course_path, "topics")
note_dir = os.path.join(course_path, "notes")

os.makedirs(topic_dir, exist_ok=True)
os.makedirs(note_dir, exist_ok=True)

topic_file = os.path.join(topic_dir, f"{content_name}.json")


# Load topics
if os.path.exists(topic_file):
    with open(topic_file, "r") as f:
        topics = json.load(f)
else:
    topics = []

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

st.markdown("""
<style>
.box {
    border: 1px solid #d3d3d3;
    border-radius: 5px;
    padding: 0px;
    margin-bottom: 1px;
    margin-top: 0px;

    background-color: #f9f9f9;
}
.module-title {
    font-weight: bold;
    font-size: 18px;
    margin-bottom: 3px;
}
.button-row {
    display: flex;
    gap: 10px;
}
</style>
""", unsafe_allow_html=True)
# Page UI
st.markdown(f"<h2 style='text-align: left; padding-top: 0px;'>📑 {content_name}</h2>", unsafe_allow_html=True)

# Content Header and Add Button in One Line
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.subheader("📌 Topics")

# Flag to control popover visibility
if "show_add_topic" not in st.session_state:
    st.session_state.show_add_topic = False

with col2:
    if not st.session_state.show_add_topic:
        if st.button("➕ Add Topic"):
            st.session_state.show_add_topic = True
            st.rerun()

# Render popover only when the flag is true
if st.session_state.show_add_topic:
    with st.expander("➕ Add Topic", expanded=True):
        new_topic = st.text_input("Enter topic name:", key="topic_input")

        if st.button("Add Topic", key="add_topic_btn"):
            if new_topic and new_topic not in topics:
                topics.append(new_topic)
                with open(topic_file, "w") as f:
                    json.dump(topics, f, indent=2)

                # Clear input and hide the popover
                st.session_state.pop("topic_input", None)
                st.session_state.show_add_topic = False
                st.success(f"Added content: {new_topic}")
                st.rerun()

# 📋 Show existing topics with editable notes
if not topics:
    st.info("No topics added yet.")
else:
    for topic in topics:
        st.markdown('<div class="box">', unsafe_allow_html=True)
        col1, col2, col3, col4 = st.columns([0.6, 0.13, 0.13, 0.14])

        with col1:
            st.markdown(f"📘 **{topic}**")

        with col2:
            if st.button("✏️ Edit", key=f"edit_{topic}"):
                st.session_state.selected_topic = topic
                st.switch_page("pages/topic_editor.py")

        with col3:
            if st.button("📇 Flashcards", key=f"flashcard_{topic}"):
                st.session_state.selected_topic_for_revision = topic
                st.switch_page("pages/revise_flashcards.py")

        with col4:
            if st.button("🗑️", key=f"delete_{topic}"):
                st.session_state.topic_to_delete = topic
                st.rerun()


        # 💬 Show confirmation below the box if this topic is selected for deletion
        if st.session_state.get("topic_to_delete") == topic:
            with st.container():
                st.markdown(
                    f"""
                    <div style="padding-left: 150px; border-radius: 5px; margin-top: -25px;">
                    <b>⚠️ Confirm deletion of topic:</b> <span style="color:#d11a2a;">{topic}</span><br>
                    """,
                    unsafe_allow_html=True
                )

                col_extra, col_confirm, col_cancel = st.columns([0.1,0.3, 0.9])
                with col_confirm:
                    if st.button("✅ Yes, Delete", key=f"confirm_delete_{topic}"):
                        topics = [t for t in topics if t != topic]
                        with open(topic_file, "w") as f:
                            json.dump(topics, f, indent=2)

                        note_path = os.path.join(note_dir, f"{content_name}_{topic}.md")
                        if os.path.exists(note_path):
                            os.remove(note_path)

                        del st.session_state.topic_to_delete
                        st.success(f"Deleted topic: {topic}")
                        st.rerun()

                with col_cancel:
                    if st.button("❌ Cancel", key=f"cancel_delete_{topic}"):
                        del st.session_state.topic_to_delete
                        st.rerun()

                # st.markdown("</div>", unsafe_allow_html=True)

        # st.markdown('</div>', unsafe_allow_html=True)
