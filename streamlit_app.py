import streamlit as st
import os
import json
import uuid
import datetime
import psutil

# --- STEP 1: Find a suitable drive and create base SmartStudy folder ---
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
    # Fallback to current directory if no external drive found
    return os.path.abspath("SmartStudy")

# --- Setup SmartStudy Path ---
SMARTSTUDY_DIR = find_smartstudy_path()
COURSE_FILE = os.path.join(SMARTSTUDY_DIR, "courses.json")
REVISION_FOLDER = os.path.join(SMARTSTUDY_DIR, "revisions")
API_KEY_FILE = os.path.join(SMARTSTUDY_DIR, "api_key.txt")

os.makedirs(REVISION_FOLDER, exist_ok=True)

# --- Load courses ---
def load_courses():
    if os.path.exists(COURSE_FILE):
        with open(COURSE_FILE, "r") as f:
            return json.load(f)
    return []

def save_courses(courses):
    with open(COURSE_FILE, "w") as f:
        json.dump(courses, f, indent=2)

courses = load_courses()

# --- Streamlit Page Config ---
st.set_page_config("Smart Revision Tracker", layout="wide")
st.markdown("""<style>.block-container {padding-top: 2rem !important;}</style>""", unsafe_allow_html=True)
# Heading with clickable name and external link
st.markdown("""
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <h2 style='margin: 0;'>Welcome 👋</h2>
        <p style='font-size: 14px; color: gray; margin: 0;'>
            Made with ❤️ by 
            <a href="https://omkar-deshmukh.vercel.app" target="_blank" style="text-decoration: none; color: #3366cc;">
                <b>Omkar Deshmukh</b>
            </a>
        </p>
    </div>
""", unsafe_allow_html=True)

# --- API Key Input / Change ---
if os.path.exists(API_KEY_FILE) and "OPENAI_API_KEY" not in st.session_state:
    with open(API_KEY_FILE, "r") as f:
        st.session_state["OPENAI_API_KEY"] = f.read().strip()

# --- Post-update success feedback ---
if st.session_state.get("api_key_updated"):
    st.success("✅ API Key updated successfully!")
    del st.session_state["api_key_updated"]

# --- Section Heading with Inline Button ---
col1, col2 = st.columns([0.7, 0.3])
with col1:
    st.markdown("### 🔐 OpenAI API Key")
with col2:
    if st.button("💡 How to get OpenAI API Key?"):
        st.session_state.show_api_key_guide = True

# --- Modal for API Key Steps ---
if st.session_state.get("show_api_key_guide", False):
    with st.expander("🧭 Steps to get OpenAI API Key", expanded=True):
        st.markdown("#### 📝 Follow these steps:")
        st.markdown("""
        **Step 1:** Go to [OpenAI API Keys Page](https://platform.openai.com/settings/organization/api-keys)  
        **Step 2:** Sign in or create an OpenAI account  
        **Step 3:** Navigate to the **API Keys** section from left dashboard   
        **Step 4:** Click on **Create new secret key**  
        **Step 5:** Copy the key and paste it into the input box below  
        """)
        if st.button("Close Guide"):
            st.session_state["show_api_key_guide"] = False
            del st.session_state.show_api_key_guide
            st.rerun()


if "OPENAI_API_KEY" in st.session_state:
    st.success("✅ OpenAI API Key is saved and active for this session.")
    with st.expander("✏️ Change API Key", expanded=False):
        new_api_key = st.text_input("Enter new API Key:", type="password", key="change_key_input")
        if st.button("Update Key"):
            if new_api_key:
                with open(API_KEY_FILE, "w") as f:
                    f.write(new_api_key.strip())
                st.session_state["OPENAI_API_KEY"] = new_api_key.strip()
                st.session_state["api_key_updated"] = True  # trigger message on rerun
                st.rerun()
else:
    with st.expander("🔑 Add OpenAI API Key", expanded=True):
        api_key_input = st.text_input("Enter your API Key:", type="password", key="initial_key_input")
        if st.button("Save API Key"):
            if api_key_input:
                with open(API_KEY_FILE, "w") as f:
                    f.write(api_key_input.strip())
                st.session_state["OPENAI_API_KEY"] = api_key_input.strip()
                st.session_state["api_key_updated"] = True
                st.rerun()


# --- Load from file if not in session ---
if "OPENAI_API_KEY" not in st.session_state and os.path.exists(API_KEY_FILE):
    with open(API_KEY_FILE, "r") as f:
        st.session_state["OPENAI_API_KEY"] = f.read().strip()

# --- Course UI ---
col1, col2 = st.columns([0.8, 0.2])
with col1:
    st.subheader("📘 Your Courses")
if "show_add_course" not in st.session_state:
    st.session_state.show_add_course = False
with col2:
    if not st.session_state.show_add_course:
        if st.button("➕ Add Course"):
            st.session_state.show_add_course = True
            st.rerun()

# --- Add Course Section ---
if st.session_state.show_add_course:
    with st.expander("➕ Add Course", expanded=True):
        new_course_name = st.text_input("Course Name", key="course_name_input")
        if st.button("Add Course"):
            if new_course_name:
                new_course = {
                    "id": str(uuid.uuid4()),
                    "name": new_course_name,
                    "created_at": datetime.datetime.now().isoformat()
                }
                courses.append(new_course)
                save_courses(courses)
                os.makedirs(f"{REVISION_FOLDER}/{new_course['id']}", exist_ok=True)
                st.session_state.pop("course_name_input", None)
                st.session_state.show_add_course = False
                st.success(f"Course '{new_course_name}' added!")
                st.rerun()

# --- Style ---
st.markdown("""
<style>
.box {
    border: 1px solid #d3d3d3;
    border-radius: 5px;
    padding: 0px;
    margin-bottom: 0px;
    background-color: #f9f9f9;
}
</style>
""", unsafe_allow_html=True)

if not courses:
    st.info("No courses added yet. Use the ➕ Add Course section above.")
else:
    container = st.container()
    col1, col2 = container.columns(2)
    for idx, course in enumerate(courses):
        with (col1 if idx % 2 == 0 else col2):
            st.markdown('<div class="box">', unsafe_allow_html=True)
            st.markdown(f"#### {course['name']}")
            st.caption(f"📅 Created: {course['created_at'][:10]}")

            if st.session_state.get("confirm_delete_course_id") == course['id']:
                st.markdown(
                    f"<div style='padding-left:100px; margin-top:-10px;'><b>⚠️ Confirm deletion of course:</b> <span style='color:#d11a2a;'>{course['name']}</span></div>",
                    unsafe_allow_html=True
                )
                spacer, col_confirm, col_cancel = st.columns([0.1, 0.5, 0.5])
                with col_confirm:
                    if st.button("✅ Yes, Delete", key=f"confirm_delete_{course['id']}"):
                        courses = [c for c in courses if c["id"] != course['id']]
                        save_courses(courses)
                        import shutil
                        shutil.rmtree(f"{REVISION_FOLDER}/{course['id']}", ignore_errors=True)
                        del st.session_state.confirm_delete_course_id
                        st.success(f"Deleted course: {course['name']}")
                        st.rerun()
                with col_cancel:
                    if st.button("❌ Cancel", key=f"cancel_delete_{course['id']}"):
                        del st.session_state.confirm_delete_course_id
                        st.rerun()
            else:
                col_open, col_delete = st.columns([1, 0.4])
                with col_open:
                    if st.button("Open", key=f"btn_{course['id']}"):
                        st.session_state.selected_course_id = course['id']
                        st.session_state.selected_course_name = course['name']
                        st.session_state.smartstudy_path = SMARTSTUDY_DIR
                        st.switch_page("pages/course_page.py")
                with col_delete:
                    if st.button("🗑️", key=f"del_{course['id']}"):
                        st.session_state.confirm_delete_course_id = course['id']
                        st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)
