import streamlit as st
import pandas as pd
from tools import get_all_progress
from agent import agent_executor
import os

st.set_page_config(page_title="Study Tools", page_icon="🧠", layout="wide")

with st.sidebar:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", use_container_width=True)  # <-- Fix here
    st.title("🎓 EduBot Exam Coach")
    st.markdown("---")

st.title("🧠 Smart Study Tools")
st.write("Use these tools to get personalized recommendations and help.")
progress_data = get_all_progress()

if not progress_data:
    st.warning(
        "No progress data found. Take some quizzes in the Chat page to use these tools!")
    st.stop()

df = pd.DataFrame(progress_data)
st.subheader("🎯 Study Technique Recommender")
st.write("Let's find the best way to study for your toughest subject.")
avg_by_topic = df.groupby('topic')['score'].mean()

if not avg_by_topic.empty:
    weakest_topic = avg_by_topic.idxmin()
    weakest_score = avg_by_topic.min()
    st.info(
        f"Your weakest topic appears to be **{weakest_topic}** with an average score of **{weakest_score:.2f}%**.")
    if st.button(f"Recommend a Study Technique for {weakest_topic}"):
        with st.spinner(f"Generating recommendation for {weakest_topic}..."):
            prompt = f"Based on my poor performance, what is a proven study technique for the topic '{weakest_topic}'? Explain it briefly."
            response = agent_executor.invoke({"input": prompt})
            st.success("Here is a recommended study technique:")
            with st.container(border=True):
                st.markdown(response['output'])
else:
    st.info("No topics with scores found.")

st.markdown("---")
st.subheader("👶 Explain Like I'm 5 (ELI5)")
eli5_topic = st.text_input("Enter a complex topic you want explained simply:")

if st.button("Explain It!"):
    if eli5_topic:
        with st.spinner(f"Simplifying {eli5_topic}..."):
            prompt = f"Explain the topic '{eli5_topic}' to me like I'm 5 years old."
            response = agent_executor.invoke({"input": prompt})
            st.success(f"Here is a simple explanation of **{eli5_topic}**:")
            with st.container(border=True):
                st.markdown(response['output'])
    else:
        st.warning("Please enter a topic to explain.")
