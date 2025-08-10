import streamlit as st
import pandas as pd
import plotly.express as px
from tools import get_all_progress
import os

st.set_page_config(page_title="Performance Dashboard",
                   page_icon="📊", layout="wide")

with st.sidebar:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", use_container_width=True)  # <-- Fix here
    st.title("🎓 EduBot Exam Coach")
    st.markdown("---")

st.title("📊 Performance Dashboard")
st.write("Here's a visual summary of your progress.")
progress_data = get_all_progress()

if not progress_data:
    st.warning(
        "No progress data found. Take some quizzes in the Chat page to see your dashboard!")
    st.stop()

df = pd.DataFrame(progress_data)
df['date'] = pd.to_datetime(df['date'])
st.subheader("Key Metrics")
avg_score = df['score'].mean()
total_quizzes = len(df)
best_topic_series = df.groupby('topic')['score'].mean()

if not best_topic_series.empty:
    best_topic = best_topic_series.idxmax()
    best_score = best_topic_series.max()
else:
    best_topic = "N/A"
    best_score = 0

col1, col2, col3 = st.columns(3)
col1.metric("Total Quizzes Taken", f"{total_quizzes}")
col2.metric("Overall Average Score", f"{avg_score:.2f}%")
col3.metric("Best Topic", f"{best_topic}", f"{best_score:.2f}% Avg")
st.markdown("---")

st.subheader("Progress Over Time")
if not df.empty:
    fig_time = px.line(df, x='date', y='score', color='topic', markers=True, title="Quiz Scores Over Time", labels={
                       "date": "Date", "score": "Score (%)", "topic": "Topic"})
    fig_time.update_layout(yaxis_range=[0, 100])
    st.plotly_chart(fig_time, use_container_width=True)

st.subheader("Performance by Topic")
if not df.empty:
    avg_by_topic = df.groupby('topic')['score'].mean().reset_index()
    fig_topic = px.bar(avg_by_topic, x='topic', y='score', title="Average Score by Topic", labels={
                       "topic": "Topic", "score": "Average Score (%)"})
    fig_topic.update_layout(yaxis_range=[0, 100])
    st.plotly_chart(fig_topic, use_container_width=True)

with st.expander("Show Raw Progress Data"):
    st.dataframe(df)
