import streamlit as st
import requests

# ---------- CONFIGURATION ----------
st.set_page_config(page_title="EduBot - Subject Tutor", layout="centered")

# ---------- SESSION STATE ----------
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "progress" not in st.session_state:
    st.session_state.progress = {"Correct": 0, "Incorrect": 0}

if "last_answer" not in st.session_state:
    st.session_state.last_answer = ""

# ---------- SUBJECT THEMES ----------
subject_colors = {
    "math": "#e6f7ff",
    "science": "#e8fce8",
    "history": "#fff3e6",
}

# ---------- UI HEADER ----------
st.markdown(f"""
    <h1 style='text-align: center;'>🎓 EduBot - Subject Tutor</h1>
    <p style='text-align: center;'>Ask questions from <b>Math</b>, <b>Science</b>, or <b>History</b>.</p>
""", unsafe_allow_html=True)

# ---------- SUBJECT & TOPIC ----------
subject = st.selectbox("📘 Choose a subject:", ["math", "science", "history"])
st.markdown(f"<div style='background-color:{subject_colors[subject]}; padding:10px; border-radius:10px;'>", unsafe_allow_html=True)

topic = st.selectbox("📚 Choose a topic:", {
    "math": ["Algebra", "Geometry", "Trigonometry"],
    "science": ["Physics", "Biology", "Chemistry"],
    "history": ["Ancient", "Medieval", "Modern"]
}[subject])

question = st.text_input("✏️ Enter your question:")

# ---------- Ask Button ----------
if st.button("Ask"):
    if not question.strip():
        st.warning("Please enter a question.")
    else:
        try:
            res = requests.post("http://127.0.0.1:8000/ask", json={"question": question, "subject": subject})
            if res.status_code == 200:
                data = res.json()
                answer = data.get("answer", "❌ No answer received.")

                # Save in history
                st.session_state.chat_history.append({
                    "question": question,
                    "answer": answer,
                    "subject": subject,
                    "topic": topic
                })
                st.session_state.last_answer = answer

                # Display answer
                st.success(answer)

                # Hint system
                if "not mentioned" in answer.lower():
                    st.info("💡 Hint: Try rephrasing your question or check if it relates to the selected topic.")

            else:
                st.error(f"❌ Error {res.status_code}: {res.text}")
        except Exception as e:
            st.error(f"🚫 Request failed: {str(e)}")

st.markdown("</div>", unsafe_allow_html=True)

# ---------- FEEDBACK ----------
if st.session_state.last_answer:
    feedback = st.radio("📝 Was this answer helpful?", ["👍 Yes", "👎 No"], horizontal=True)
    if feedback == "👍 Yes":
        st.session_state.progress["Correct"] += 1
    elif feedback == "👎 No":
        st.session_state.progress["Incorrect"] += 1

# ---------- CHAT HISTORY ----------
if st.session_state.chat_history:
    st.markdown("### 🗂️ Previous Q&A")
    for entry in reversed(st.session_state.chat_history[-5:]):  # last 5 only
        st.markdown(f"**Q:** ({entry['subject'].capitalize()} - {entry['topic']}) {entry['question']}")
        st.markdown(f"<div style='margin-left:20px; color:#444;'>💬 {entry['answer']}</div>", unsafe_allow_html=True)
        st.markdown("---")

# ---------- PROGRESS TRACKER ----------
st.markdown("### 📈 Your Progress")
st.progress(int(100 * st.session_state.progress["Correct"] / (st.session_state.progress["Correct"] + st.session_state.progress["Incorrect"] + 1e-5)))
st.markdown(f"✅ Correct: {st.session_state.progress['Correct']} | ❌ Incorrect: {st.session_state.progress['Incorrect']}")
