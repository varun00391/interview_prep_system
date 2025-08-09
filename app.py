import streamlit as st
import requests
from io import BytesIO

# =========================
# CONFIG
# =========================
API_URL = "http://localhost:8000/generate-questions"  # Change if deployed

# =========================
# PAGE SETTINGS
# =========================
st.set_page_config(page_title="Resume Question Generator", layout="centered")
st.title("📄 AI Resume Interview Question Generator")

st.write("Upload a PDF resume and get 4 rounds of interview questions generated using Groq's LLM.")

# =========================
# FILE UPLOAD
# =========================
uploaded_file = st.file_uploader("Upload Resume PDF", type=["pdf"])

if uploaded_file is not None:
    if st.button("Generate Questions"):
        with st.spinner("Generating questions... ⏳"):
            try:
                # Send PDF to FastAPI
                files = {"file": (uploaded_file.name, uploaded_file, "application/pdf")}
                response = requests.post(API_URL, files=files)

                if response.status_code != 200:
                    st.error(f"Error: {response.json().get('detail', 'Unknown error')}")
                else:
                    data = response.json()

                    # Display results
                    for round_name, questions in data.items():
                        st.subheader(round_name.replace("_", " ").title())
                        for i, q in enumerate(questions, start=1):
                            st.markdown(f"**Q{i}:** {q['question']}")
                            if q.get("notes"):
                                st.markdown(f"*Notes:* {q['notes']}")

            except Exception as e:
                st.error(f"An error occurred: {e}")
