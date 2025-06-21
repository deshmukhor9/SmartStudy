import streamlit as st
import os
import json
import psutil

# --- Find suitable drive for SmartStudy storage ---
def find_smartstudy_path():
    for part in psutil.disk_partitions():
        if part.device.startswith("C:"):
            continue  # Skip system drive
        try:
            base = os.path.join(part.device, "SmartStudy")
            os.makedirs(base, exist_ok=True)
            return base
        except:
            continue
    return os.path.abspath("SmartStudy")  # fallback

# --- Set base SmartStudy directory ---
SMARTSTUDY_DIR = find_smartstudy_path()

# --- Validate session ---
if "selected_course_id" not in st.session_state or "selected_course_name" not in st.session_state:
    st.error("No course selected. Please go back and choose a course.")
    st.stop()

course_id = st.session_state.selected_course_id
course_name = st.session_state.selected_course_name

# ✅ All folders will now go under SmartStudy
course_path = os.path.join(SMARTSTUDY_DIR, "revisions", course_id)
content_file = os.path.join(course_path, "content_list.json")
os.makedirs(course_path, exist_ok=True)


# Load content
if os.path.exists(content_file):
    with open(content_file, "r") as f:
        content_list = json.load(f)
else:
    content_list = []

st.markdown("""
    <style>
    /* Remove top padding Streamlit adds */
    .block-container {
        padding-top: 3rem !important;
    }
    </style>
""", unsafe_allow_html=True)
if st.button("← Back", key="back_button"):
    st.switch_page("streamlit_app.py")  # Adjust to the actual page you're returning to

# Title
st.markdown(f"<h2 style='text-align: left ;'>📘 {course_name}</h2>", unsafe_allow_html=True)
# Content Header and Add Button in One Line
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.subheader("🧩 Content")

# Flag to control popover visibility
if "show_add_content" not in st.session_state:
    st.session_state.show_add_content = False

with col2:
    if not st.session_state.show_add_content:
        if st.button("➕ Add Content"):
            st.session_state.show_add_content = True
            st.rerun()

# Render popover only when the flag is true
if st.session_state.show_add_content:
    with st.expander("➕ Add Content", expanded=True):
        new_content = st.text_input("Enter new content", key="content_input")

        if st.button("Add Content", key="add_content_btn"):
            if new_content and new_content not in content_list:
                content_list.append(new_content)
                with open(content_file, "w") as f:
                    json.dump(content_list, f, indent=2)

                # Clear input and hide the popover
                st.session_state.pop("content_input", None)
                st.session_state.show_add_content = False
                st.success(f"Added content: {new_content}")
                st.rerun()

# Inject custom CSS for box-style
st.markdown("""
<style>
.box {
    border: 1px solid #d3d3d3;
    border-radius: 5px;
    padding: 0px;
    margin-bottom: 10px;
    margin-top: -5px;
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

# 📂 Display in 2 columns with styled boxes
col1, col2 = st.columns(2)

for idx, item in enumerate(content_list):
    with (col1 if idx % 2 == 0 else col2):
        st.markdown('<div class="box">', unsafe_allow_html=True)
        st.markdown(f'<div class="module-title">🔹 {item}</div>', unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns([0.2, 0.2, 0.2, 0.2])
        with c1:
            if st.button("Open", key=f"open_{item}"):
                st.session_state.selected_content = item
                st.switch_page("pages/topic_page.py")

        with c2:
            if st.button("Revise", key=f"revise_{item}"):
                st.session_state.selected_content_for_revision = item
                st.switch_page("pages/revise_flashcards.py")
        with c3:
            if st.button("Quiz", key=f"quiz_{item}"):
                st.session_state.selected_content_for_quiz = item
                st.session_state.quiz_content_name = item  # ✅ Needed for quiz_mcq.py
                st.switch_page("pages/quiz_page.py")
        with c4:
            if st.button("🗑️", key=f"delete_{item}"):
                st.session_state.confirm_delete_content = item
                st.rerun()

        # Deletion confirmation block (inline)
        if st.session_state.get("confirm_delete_content") == item:
            st.markdown(
                f"""
                <div style="padding-left: 100px; margin-top: -15px;">
                <b>⚠️ Confirm deletion of content:</b> <span style="color:#d11a2a;">{item}</span><br>
                </div>
                """,
                unsafe_allow_html=True
            )

            spacer, col_confirm, col_cancel = st.columns([0.12, 0.25, 0.4])
            with col_confirm:
                if st.button("✅ Yes, Delete", key=f"confirm_delete_{item}"):
                    content_list = [c for c in content_list if c != item]
                    with open(content_file, "w") as f:
                        json.dump(content_list, f, indent=2)

                    # Also remove associated topic/note folders (optional cleanup)
                    # --- START: Cleanup associated files ---
                    # 1. Delete topic metadata JSON
                    topic_file = os.path.join(course_path, "topics", f"{item}.json")
                    if os.path.exists(topic_file):
                        os.remove(topic_file)

                    # 2. Delete related note files
                    notes_folder = os.path.join(course_path, "notes")
                    if os.path.exists(notes_folder):
                        for note_file in os.listdir(notes_folder):
                            if note_file.startswith(f"{item}_"):
                                os.remove(os.path.join(notes_folder, note_file))

                    # 3. Delete related flashcards (both content-level and topic-level)
                    flashcards_folder = os.path.join(course_path, "flashcards")
                    if os.path.exists(flashcards_folder):
                        for flash_file in os.listdir(flashcards_folder):
                            if flash_file == f"{item}.md" or flash_file.startswith(f"{item}_"):
                                os.remove(os.path.join(flashcards_folder, flash_file))
                  
                    quiz_folder = os.path.join(course_path, "quiz")
                    if os.path.exists(quiz_folder):
                        for quiz_file in os.listdir(quiz_folder):
                            if quiz_file == f"{item}.json" or quiz_file.startswith(f"{item}_"):
                                os.remove(os.path.join(quiz_folder, quiz_file))
                    # --- END: Cleanup associated files ---

                    # if os.path.exists(content_topic):
                    #     os.remove(content_topic)
                    # # If you have per-topic notes under notes folder
                    # for note_file in os.listdir(content_note):
                    #     if note_file.startswith(f"{item}_"):
                    #         os.remove(os.path.join(content_note, note_file))

                    del st.session_state.confirm_delete_content
                    st.success(f"Deleted '{item}'")
                    st.rerun()

            with col_cancel:
                if st.button("❌ Cancel", key=f"cancel_delete_{item}"):
                    del st.session_state.confirm_delete_content
                    st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)  # Close .box div
