import streamlit as st
import json
import os
from agent import agent_executor
from tools import save_quiz_result, generate_quiz

# --- App Configuration ---
st.set_page_config(page_title="EduBot Exam Coach",
                   page_icon="🤖", layout="wide")

# --- Sidebar ---
with st.sidebar:
    if os.path.exists("assets/logo.png"):
        st.image("assets/logo.png", use_container_width=True)
    st.title("🎓 EduBot Exam Coach")
    st.markdown("---")
    st.markdown("Welcome! Navigate between Chat, Dashboard, and Study Tools.")
    st.markdown("---")

# --- Main Page ---
st.title("🤖 EduBot Chat")

# --- Initialize Session State ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "Hello! Ask me to create a quiz, make a revision plan, or ask a question about your study material."}]
if "in_quiz" not in st.session_state:
    st.session_state.in_quiz = False
if "quiz_questions" not in st.session_state:
    st.session_state.quiz_questions = []
if "current_question_index" not in st.session_state:
    st.session_state.current_question_index = 0
if "user_answers" not in st.session_state:
    st.session_state.user_answers = []
if "quiz_topic" not in st.session_state:
    st.session_state.quiz_topic = ""

# --- Helper function to start a quiz ---


def start_quiz(quiz_json_string, topic):
    try:
        clean_json_string = quiz_json_string.strip().replace(
            "```json", "").replace("```", "")
        parsed_quiz = json.loads(clean_json_string)
        if isinstance(parsed_quiz, dict):
            st.session_state.quiz_questions = list(parsed_quiz.values())
        else:
            st.session_state.quiz_questions = parsed_quiz
        if not isinstance(st.session_state.quiz_questions, list) or len(st.session_state.quiz_questions) == 0:
            raise ValueError("Quiz data is not a valid list of questions.")
        st.session_state.in_quiz = True
        st.session_state.current_question_index = 0
        st.session_state.user_answers = []
        st.session_state.quiz_topic = topic
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        st.error(
            f"There was an issue starting the quiz: {e}. The AI may have produced an invalid format. Please ask for the quiz again.")
        st.session_state.in_quiz = False


# --- Display Chat History ---
for message in st.session_state.messages:
    avatar_icon = "🤖" if message["role"] == "assistant" else "👤"
    with st.chat_message(message["role"], avatar=avatar_icon):
        st.markdown(message["content"])

# --- Main App Logic ---
if st.session_state.in_quiz:
    idx = st.session_state.current_question_index
    if idx < len(st.session_state.quiz_questions):
        q = st.session_state.quiz_questions[idx]
        with st.chat_message("assistant", avatar="🤖"):
            st.write(
                f"**Question {idx + 1}/{len(st.session_state.quiz_questions)}:**")
            st.write(q.get("question", "No question text found."))
            with st.form(key=f"question_{idx}"):
                options = q.get("options", [])
                if options and isinstance(options, list):
                    user_answer = st.radio(
                        "Choose your answer:", options, key=f"radio_{idx}")
                else:
                    st.write("No options provided.")
                    user_answer = ""
                submitted = st.form_submit_button("Submit Answer")
                if submitted:
                    st.session_state.user_answers.append(user_answer)
                    correct_answer_from_ai = q.get("correct_answer")
                    correct_answer_text = ""
                    if isinstance(correct_answer_from_ai, int) and correct_answer_from_ai < len(options):
                        correct_answer_text = options[correct_answer_from_ai]
                    elif isinstance(correct_answer_from_ai, str):
                        correct_answer_text = correct_answer_from_ai

                    if user_answer == correct_answer_text:
                        st.success("Correct! 🎉")
                    else:
                        st.error(
                            f"Incorrect. The correct answer was: {correct_answer_text}")
                    st.info(
                        f"**Rationale:** {q.get('rationale', 'No rationale provided.')}")
                    st.session_state.current_question_index += 1
                    st.rerun()
    else:
        # --- QUIZ FINISHED SCREEN ---
        st.session_state.in_quiz = False
        correct_answers = 0
        for i, q in enumerate(st.session_state.quiz_questions):
            options = q.get("options", [])
            correct_answer_from_ai = q.get("correct_answer")
            correct_answer_text = ""
            if isinstance(correct_answer_from_ai, int) and correct_answer_from_ai < len(options):
                correct_answer_text = options[correct_answer_from_ai]
            elif isinstance(correct_answer_from_ai, str):
                correct_answer_text = correct_answer_from_ai
            if i < len(st.session_state.user_answers) and st.session_state.user_answers[i] == correct_answer_text:
                correct_answers += 1

        score_percent = int((correct_answers / len(st.session_state.quiz_questions))
                            * 100) if st.session_state.quiz_questions else 0
        final_message = f"Quiz complete! You scored {correct_answers} out of {len(st.session_state.quiz_questions)} ({score_percent}%)."

        with st.chat_message("assistant", avatar="🤖"):
            st.header(final_message)

        with st.spinner("Saving your score..."):
            save_quiz_result(
                f"I scored {score_percent}% in {st.session_state.quiz_topic} quiz")
        st.success("Your score has been saved to your progress tracker!")
        st.session_state.messages.append(
            {"role": "assistant", "content": final_message})

        # --- NEW QUIZ REVIEW SECTION ---
        with st.expander("📝 Review Your Answers"):
            for i, q in enumerate(st.session_state.quiz_questions):
                st.markdown("---")
                st.write(f"**Question {i+1}:** {q.get('question')}")

                user_ans = st.session_state.user_answers[i]
                options = q.get("options", [])
                correct_answer_from_ai = q.get("correct_answer")
                correct_answer_text = ""

                if isinstance(correct_answer_from_ai, int) and correct_answer_from_ai < len(options):
                    correct_answer_text = options[correct_answer_from_ai]
                elif isinstance(correct_answer_from_ai, str):
                    correct_answer_text = correct_answer_from_ai

                if user_ans == correct_answer_text:
                    st.success(f"Your answer: {user_ans} ✅")
                else:
                    st.error(f"Your answer: {user_ans} ❌")
                    st.info(f"Correct answer: {correct_answer_text}")

                st.write(f"**Rationale:** {q.get('rationale')}")

        # This button resets the state to allow chatting again
        if st.button("Continue Chatting"):
            st.session_state.in_quiz = False
            st.session_state.quiz_questions = []
            st.session_state.user_answers = []
            st.session_state.current_question_index = 0
            st.session_state.quiz_topic = ""
            st.rerun()

else:
    if prompt := st.chat_input("What would you like to do?"):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user", avatar="👤"):
            st.markdown(prompt)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Thinking..."):
                try:
                    if "quiz" in prompt.lower():
                        quiz_json_string = generate_quiz(prompt)
                        start_quiz(quiz_json_string, prompt)
                        st.rerun()
                    else:
                        response = agent_executor.invoke({"input": prompt})
                        output = response['output']
                        st.markdown(output)
                        st.session_state.messages.append(
                            {"role": "assistant", "content": output})
                except Exception as e:
                    error_message = f"An error occurred: {e}"
                    st.error(error_message)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_message})
