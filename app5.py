import streamlit as st
from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import wikipedia
from googlesearch import search
import requests
from fpdf import FPDF
import os

# 🔐 Set Groq API Key
os.environ["GROQ_API_KEY"] = "3FY8kolHmcxjmlXbHc0FpRGUsm3"
llm = ChatGroq(model_name="llama-3.1-8b-instant", temperature=0.2)

# 📚 Helper: Wikipedia Summary
def get_wiki_summary(topic):
    try:
        summary = wikipedia.summary(topic, sentences=3)
        url = wikipedia.page(topic).url
        return summary, url
    except:
        return "No Wikipedia summary found.", "#"

# 🎥 Helper: YouTube Links via Google Search
def get_youtube_links(query, max_results=3):
    results = []
    try:
        for url in search(f"{query} site:youtube.com", num_results=max_results):
            if "youtube.com/watch" in url:
                results.append(url)
    except:
        results = ["No videos found."]
    return results

# 📘 Helper: Book Recommendations (OpenLibrary)
def get_books_from_openlibrary(query, max_results=3):
    url = f"https://openlibrary.org/search.json?q={query}"
    try:
        response = requests.get(url)
        results = response.json()
        books = []
        for doc in results.get("docs", [])[:max_results]:
            title = doc.get("title", "Unknown Title")
            author = ", ".join(doc.get("author_name", ["Unknown Author"]))
            year = doc.get("first_publish_year", "N/A")
            link = f"https://openlibrary.org{doc.get('key', '')}"
            books.append(f"📘 [{title} by {author} ({year})]({link})")
        return books if books else ["No books found."]
    except Exception as e:
        return [f"Error: {str(e)}"]

# 📄 Helper: Save Answer to PDF
def save_to_pdf(content, filename="EduBot_Output.pdf"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    for line in content.split('\n'):
        pdf.multi_cell(0, 10, line)
    pdf.output(filename)
    return filename

# 🎨 UI Setup
st.set_page_config(page_title="EduBot AI", layout="wide", page_icon="🎓")
col1, col2, col3 = st.columns([1, 6, 1])
with col2:
    st.markdown("<h1 style='text-align: center; color: #1f77b4;'>🎓 EduBot - Your AI Homework Assistant</h1>", unsafe_allow_html=True)

subjects = ["Math", "Science", "English", "History", "Computer Science"]

# Sidebar
with st.sidebar:
    st.markdown("## 🧰 **EduBot Tools**")
    tool = st.selectbox("🔧 Select Tool", ["📘 Solve Homework", "📝 Create Quiz", "✅ Submission Checker"])
    subject = st.selectbox("📚 Choose Subject", subjects)
    st.markdown("---")
    st.markdown("🌐 [GitHub](https://github.com/ABHISHEK-ai-web) | ✉️ [Contact Us](mailto:abhishek200325@gmail.com)")

if "history" not in st.session_state:
    st.session_state.history = []

# 📘 Solve Homework
if tool == "📘 Solve Homework":
    question = st.text_area("✍️ Enter your homework question")
    if st.button("🚀 Solve Now") and question:
        with st.spinner("AI solving your question..."):
            # Answer
            prompt = PromptTemplate(
                input_variables=["subject", "question"],
                template="""
                You are an expert {subject} tutor. Solve this question:
                {question}
                Provide a clear, step-by-step explanation.
                """
            )
            chain = LLMChain(llm=llm, prompt=prompt)
            answer = chain.run({"subject": subject, "question": question})
            st.success("✅ Answer:")
            st.markdown(f"```markdown\n{answer}\n```")

            # Wikipedia
            summary, url = get_wiki_summary(question)
            with st.expander("🌐 Wikipedia Summary"):
                st.info(summary)
                st.markdown(f"[🔗 Open Wikipedia]({url})")

            # YouTube
            with st.expander("📺 YouTube Lectures"):
                for link in get_youtube_links(question):
                    st.markdown(f"- [Watch Video]({link})")

            # Books
            with st.expander("📚 Book Recommendations"):
                for book in get_books_from_openlibrary(question):
                    st.markdown(book)

            # Study Plan
            plan_prompt = PromptTemplate(
                input_variables=["subject", "topic"],
                template="""
                Create a 3-day study plan to learn the topic "{topic}" in {subject}.
                Format it as day-wise bullet points.
                """
            )
            plan_chain = LLMChain(llm=llm, prompt=plan_prompt)
            plan = plan_chain.run({"subject": subject, "topic": question})
            with st.expander("🧠 AI Study Plan"):
                st.markdown(f"```markdown\n{plan}\n```")

            # Download PDF
            st.download_button("📥 Download Answer as PDF", data=answer, file_name="solution.pdf")
            st.session_state.history.append({"tool": "Solve Homework", "question": question, "answer": answer})

# 📝 Create Quiz
elif tool == "📝 Create Quiz":
    topic = st.text_input("Enter topic for quiz")
    num_q = st.slider("Number of Questions", 1, 10, 5)
    if st.button("🎯 Generate Quiz") and topic:
        with st.spinner("Generating quiz..."):
            prompt = PromptTemplate(
                input_variables=["subject", "topic", "num_questions"],
                template="""
                Create a quiz with {num_questions} questions on the topic "{topic}" in subject {subject}.
                Provide 4 options (A, B, C, D) and mark the correct answer.
                Format:
                Q1: ...
                A) ... B) ... C) ... D) ...
                Answer: ...
                """
            )
            chain = LLMChain(llm=llm, prompt=prompt)
            result = chain.run({"subject": subject, "topic": topic, "num_questions": num_q})
            st.success("✅ Quiz Generated:")
            st.markdown(f"```markdown\n{result}\n```")
            st.download_button("📥 Download Quiz", data=result, file_name="quiz.pdf")
            st.session_state.history.append({"tool": "Create Quiz", "question": topic, "answer": result})

# ✅ Submission Checker
elif tool == "✅ Submission Checker":
    question = st.text_area("📌 Original Question")
    student_ans = st.text_area("🧑‍🎓 Student's Answer")
    if st.button("🔍 Evaluate Submission") and question and student_ans:
        with st.spinner("Analyzing..."):
            prompt = PromptTemplate(
                input_variables=["subject", "question_text", "student_answer"],
                template="""
                You are a {subject} teacher. Review the student's answer:
                Question: {question_text}
                Answer: {student_answer}
                Give feedback on correctness, clarity, and improvements. Provide the correct answer too.
                """
            )
            chain = LLMChain(llm=llm, prompt=prompt)
            feedback = chain.run({
                "subject": subject,
                "question_text": question,
                "student_answer": student_ans
            })
            st.success("📘 Feedback:")
            st.markdown(f"```markdown\n{feedback}\n```")
            st.download_button("📥 Download Feedback", data=feedback, file_name="feedback.pdf")
            st.session_state.history.append({"tool": "Submission Checker", "question": question, "answer": feedback})

# 📜 Session History
st.markdown("---")
with st.expander("📜 Session History"):
    if st.session_state.history:
        for i, entry in enumerate(reversed(st.session_state.history)):
            st.markdown(f"""
            <div style="border:1px solid #ccc; padding:10px; border-radius:10px; margin-bottom:10px;">
                <strong>{entry['tool']} #{i+1}</strong><br>
                <em>📝 {entry['question']}</em><br>
                <pre>{entry['answer']}</pre>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No history yet.")
