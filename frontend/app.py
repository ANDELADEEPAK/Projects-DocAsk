import os
import streamlit as st
import requests

# --------------------------------
# CONFIGURATION
# --------------------------------

# API_URL = os.getenv("DOCASK_API_URL", "http://127.0.0.1:8000")
API_URL = st.secrets.get(
    "DOCASK_API_URL",
    os.getenv("DOCASK_API_URL", "http://127.0.0.1:8000")
)


st.set_page_config(
    page_title="DocAsk | AI Document Assistant",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --------------------------------
# SESSION STATE
# --------------------------------

if "filenames" not in st.session_state:
    st.session_state.filenames = []

if "selected_document" not in st.session_state:
    st.session_state.selected_document = None

if "messages" not in st.session_state:
    st.session_state.messages = []

# --------------------------------
# CUSTOM CSS
# --------------------------------

st.markdown("""
<style>

/* Application background */
.stApp {
    background: #0b1120;
    color: #f1f5f9;
}

/* Center application with margins */
.block-container {
    max-width: 1250px;
    padding: 2rem 2.5rem 3rem 2.5rem;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: #111827;
    border-right: 1px solid #263449;
}

/* Main application container */
.main .block-container {
    background: #111827;
    border: 1px solid #29374d;
    border-radius: 18px;
    margin-top: 25px;
    margin-bottom: 25px;
    padding: 35px 40px;
    box-shadow: 0 8px 35px rgba(0,0,0,0.25);
}

/* Header */
.main-title {
    font-size: 46px;
    font-weight: 800;
    color: #ffffff;
    margin-bottom: 0;
}

.subtitle {
    color: #94a3b8;
    font-size: 17px;
    margin-top: 8px;
}

/* Welcome card */
.info-card {
    background: #1a2638;
    border: 1px solid #34445c;
    border-radius: 15px;
    padding: 25px;
    margin: 20px 0;
}

/* Buttons */
.stButton button {
    border-radius: 10px;
    font-weight: 600;
    min-height: 42px;
}

/* Chat messages */
div[data-testid="stChatMessage"] {
    background: #1a2638;
    border: 1px solid #293b53;
    border-radius: 14px;
    padding: 15px;
    margin-bottom: 15px;
}

/* Chat input */
div[data-testid="stChatInput"] {
    border: 1px solid #34445c;
    border-radius: 14px;
}

/* Footer */
.footer {
    text-align: center;
    color: #64748b;
    font-size: 13px;
    padding: 25px;
}

</style>
""", unsafe_allow_html=True)

# --------------------------------
# BACKEND STATUS
# --------------------------------

def check_backend():
    try:
        response = requests.get(
            f"{API_URL}/health",
            timeout=(3, 5)
        )
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


# --------------------------------
# SIDEBAR
# --------------------------------

with st.sidebar:

    st.markdown("## 📚 DocAsk")

    st.caption("Your AI-powered document assistant")

    st.divider()

    st.markdown("### 📄 Upload Documents")

    uploaded_files = st.file_uploader(
        "Select PDF files",
        type=["pdf"],
        accept_multiple_files=True
    )

    if st.button("⬆️ Upload PDFs", type="primary"):

        if not uploaded_files:
            st.warning("Please select at least one PDF.")

        else:

            for uploaded_file in uploaded_files:

                try:

                    files = {
                        "file": (
                            uploaded_file.name,
                            uploaded_file.getvalue(),
                            "application/pdf"
                        )
                    }

                    with st.spinner(
                        f"Processing {uploaded_file.name}..."
                    ):

                        response = requests.post(
                            f"{API_URL}/upload",
                            files=files,
                            timeout=(10, 600)
                        )

                    if response.status_code == 200:

                        result = response.json()

                        if uploaded_file.name not in st.session_state.filenames:
                            st.session_state.filenames.append(
                                uploaded_file.name
                            )

                        st.success(
                            f"{uploaded_file.name} uploaded!"
                        )

                        st.caption(
                            f"Chunks created: {result.get('total_chunks', 0)}"
                        )

                    else:
                        st.error(f"Upload failed: {response.text}")

                except requests.exceptions.RequestException as e:
                    st.error(f"Connection error: {e}")

    st.divider()

    st.markdown("### 📂 Your Documents")

    if st.session_state.filenames:

        selected_document = st.selectbox(
            "Select a document",
            st.session_state.filenames,
            index=(
                st.session_state.filenames.index(
                    st.session_state.selected_document
                )
                if st.session_state.selected_document
                in st.session_state.filenames
                else 0
            )
        )

        st.session_state.selected_document = selected_document

    else:

        st.info("No documents uploaded yet.")

    st.divider()

    if st.button("🗑️ Clear Conversation"):
        st.session_state.messages = []
        st.rerun()

    st.markdown("### ⚙️ System Status")

    if check_backend():
        st.success("Backend Connected")
    else:
        st.error("Backend Offline")

    st.caption("Powered by Gemini AI")


# --------------------------------
# MAIN HEADER
# --------------------------------

st.markdown(
    '<div class="main-title">📚 DocAsk</div>',
    unsafe_allow_html=True
)

st.markdown(
    '<div class="subtitle">'
    'Chat with your documents using Artificial Intelligence.'
    '</div>',
    unsafe_allow_html=True
)

st.divider()

# --------------------------------
# WELCOME SECTION
# --------------------------------

if not st.session_state.messages:

    st.markdown("### 👋 Welcome to DocAsk!")

    st.markdown("""
    <div class="info-card">
        <h3>Ask questions. Understand documents. Save time.</h3>
        <p style="color:#94a3b8;">
        Upload your PDF documents and interact with their contents
        using AI-powered Retrieval-Augmented Generation (RAG).
        </p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("#### 📄")
        st.markdown("**Upload PDFs**")
        st.caption("Upload your documents.")

    with col2:
        st.markdown("#### 🔍")
        st.markdown("**Find Information**")
        st.caption("Retrieve relevant content.")

    with col3:
        st.markdown("#### 🤖")
        st.markdown("**Ask Questions**")
        st.caption("Get AI-generated answers.")


# --------------------------------
# CHAT HISTORY
# --------------------------------

for message in st.session_state.messages:

    with st.chat_message(message["role"]):

        st.markdown(message["content"])


# --------------------------------
# CHAT INPUT
# --------------------------------

question = st.chat_input(
    "Ask anything about your selected document..."
)

if question:

    selected_filename = st.session_state.selected_document

    if not selected_filename:

        st.warning("Please upload and select a PDF first.")

    else:

        st.session_state.messages.append({
            "role": "user",
            "content": question
        })

        with st.chat_message("user"):
            st.markdown(question)

        with st.chat_message("assistant"):

            with st.spinner("DocAsk is thinking..."):

                try:

                    response = requests.post(
                        f"{API_URL}/ask",
                        json={
                            "question": question,
                            "filename": selected_filename
                        },
                        timeout=(10, 300)
                    )

                    if response.status_code == 200:

                        result = response.json()
                        answer = result["answer"]

                        st.markdown(answer)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": answer
                        })

                    else:

                        error_message = (
                            f"Unable to generate an answer: "
                            f"{response.text}"
                        )

                        st.error(error_message)

                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": error_message
                        })

                except requests.exceptions.RequestException as e:

                    error_message = f"Backend connection error: {e}"

                    st.error(error_message)

                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_message
                    })


# --------------------------------
# FOOTER
# --------------------------------

st.markdown("""
<div class="footer">
    DocAsk | Built with Python · FastAPI · Gemini · ChromaDB · Streamlit
    <br>
    AI-powered document intelligence.
</div>
""", unsafe_allow_html=True)